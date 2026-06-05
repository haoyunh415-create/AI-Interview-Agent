"""Multi-agent interview orchestrator — coordinates all agents through the
interview lifecycle via SharedMemory and MessageBus.
"""

import time
from typing import Any

from agents.evaluator import PARSE_ERROR_KEY, Evaluator
from agents.interviewer import Interviewer
from agents.knowledge_retriever import KnowledgeRetriever
from agents.report_writer import ReportWriter
from agents.resume_analyst import ResumeAnalyst
from core.constants import STAGES
from core.logging_config import get_logger, log_duration
from core.memory import MessageBus, SharedMemory
from core.telemetry import TelemetryCollector
from backend.db.database import save

_log = get_logger("orchestrator")


class InterviewOrchestrator:
    """Coordinates all agents through the interview lifecycle."""

    def __init__(
        self,
        api_key: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key
        self._provider = provider
        self._model = model

        self.shared_memory = SharedMemory()
        self.message_bus = MessageBus(max_history=500)
        self.telemetry = TelemetryCollector(max_traces=500)

        self.resume_analyst = ResumeAnalyst(
            api_key, self.shared_memory, self.message_bus, self.telemetry,
            provider=provider, model=model,
        )
        self.interviewer = Interviewer(
            api_key, self.shared_memory, self.message_bus, self.telemetry,
            provider=provider, model=model,
        )
        self.evaluator = Evaluator(
            api_key, self.shared_memory, self.message_bus, self.telemetry,
            provider=provider, model=model,
        )
        self.report_writer = ReportWriter(
            api_key, self.shared_memory, self.message_bus, self.telemetry,
            provider=provider, model=model,
        )
        self.knowledge_retriever = KnowledgeRetriever(
            api_key, self.shared_memory, self.message_bus, self.telemetry,
            provider=provider, model=model,
        )

        self._setup_subscriptions()
        self._status: str = "idle"
        self._followup_count: int = 0
        self._agent_log: list[dict[str, Any]] = []

    def _setup_subscriptions(self) -> None:
        self.message_bus.subscribe_all(self._on_any_event)

    def _on_any_event(self, msg: Any) -> None:
        self._agent_log.append({
            "type": msg.type,
            "source": msg.source,
            "time": time.strftime("%H:%M:%S"),
            "data_keys": list(msg.data.keys()),
        })
        if len(self._agent_log) > 200:
            self._agent_log.pop(0)

    def agent_status(self) -> list[tuple[str, str]]:
        has_profile = self.shared_memory.get("resume.profile") is not None
        return [
            ("简历分析师", "ready" if has_profile else "待分析"),
            ("面试官", "ready" if self._status in ("questioning", "scored", "followup") else "等待中"),
            ("评价官", "ready" if self._status == "evaluating" else "等待中"),
            ("报告生成官", "ready" if self._status == "completed" else "等待中"),
        ]

    def analyze_resume(self, resume_text: str) -> dict[str, Any] | None:
        if resume_text and resume_text.strip():
            cached = self.shared_memory.get("resume.profile")
            if cached is not None:
                return cached
            profile = self.resume_analyst.analyze(resume_text)
        else:
            profile = None
            self.shared_memory.set("resume.profile", {"tech_stack": []}, "orchestrator")
        return profile

    def retrieve_context(self, topic: str) -> str:
        context = self.knowledge_retriever.retrieve(topic)
        return context

    def generate_question(
        self,
        topic: str,
        stage_idx: int,
        history: list[dict[str, str]] | None = None,
        custom_questions: list[str] | None = None,
    ) -> str:
        self._followup_count = 0
        stage = STAGES[stage_idx]
        self._status = "questioning"
        return self.interviewer.generate_question(
            topic=topic, stage=stage, context="",
            history=history, profile=None, custom_questions=custom_questions,
        )

    def generate_followup(
        self,
        original_question: str,
        answer: str,
        evaluation: dict[str, Any],
        stage_idx: int,
    ) -> str:
        stage = STAGES[stage_idx]
        self._status = "followup"
        self._followup_count += 1
        return self.interviewer.generate_followup(
            original_question=original_question,
            answer=answer, evaluation=evaluation, stage=stage,
        )

    def evaluate_answer(
        self,
        user: str,
        topic: str,
        question: str,
        answer: str,
        stage_idx: int,
        session_id: str | None = None,
    ) -> tuple[dict[str, Any], str, bool]:
        stage = STAGES[stage_idx]
        self._status = "evaluating"
        t0 = time.monotonic()

        try:
            score_json = self.evaluator.evaluate(
                question, answer, stage, self._followup_count, topic=topic,
            )
        except ValueError as e:
            _log.error("evaluation failed: %s", e)
            score_json = {
                "correctness": 0, "logic": 0, "depth": 0, "expression": 0,
                "summary": f"评分解析失败，请重试。错误: {e}",
                "improvement": "LLM 输出格式异常，建议重新提交答案",
                "needs_followup": False, "followup_reason": "",
                PARSE_ERROR_KEY: True,
            }

        save(user, topic, question, answer, score_json, stage, session_id=session_id)
        needs_followup = self.evaluator.should_followup(score_json)
        log_duration(_log, f"evaluate stage={stage} followup={needs_followup}", t0)
        report = self.evaluator.format_report(score_json)
        self._status = "scored"
        return score_json, report, needs_followup

    def evaluate_answer_stream(
        self,
        user: str, topic: str, question: str, answer: str,
        stage_idx: int, session_id: str | None = None,
    ):
        stage = STAGES[stage_idx]
        self._status = "evaluating"
        t0 = time.monotonic()
        try:
            yield from self.evaluator.evaluate_stream(
                question, answer, stage, self._followup_count, topic=topic,
            )
            score_json = self.shared_memory.get("eval.latest", {})
        except ValueError as e:
            _log.error("evaluation stream failed: %s", e)
            score_json = {
                "correctness": 0, "logic": 0, "depth": 0, "expression": 0,
                "summary": f"评分解析失败，请重试。错误: {e}",
                "improvement": "LLM 输出格式异常，建议重新提交答案",
                "needs_followup": False, "followup_reason": "",
                PARSE_ERROR_KEY: True,
            }
            self.shared_memory.set("eval.latest", score_json, "orchestrator")
        save(user, topic, question, answer, score_json, stage, session_id=session_id)
        log_duration(_log, f"evaluate_stream stage={stage}", t0)
        self._status = "scored"

    def generate_question_stream(
        self, topic: str, stage_idx: int, history: list[dict[str, str]] | None = None,
        custom_questions: list[str] | None = None,
    ):
        self._followup_count = 0
        stage = STAGES[stage_idx]
        self._status = "questioning"
        yield from self.interviewer.generate_question_stream(
            topic=topic, stage=stage, context="",
            history=history, profile=None, custom_questions=custom_questions,
        )

    def generate_followup_stream(
        self, original_question: str, answer: str,
        evaluation: dict[str, Any], stage_idx: int,
    ):
        stage = STAGES[stage_idx]
        self._status = "followup"
        self._followup_count += 1
        yield from self.interviewer.generate_followup_stream(
            original_question=original_question, answer=answer,
            evaluation=evaluation, stage=stage,
        )

    def generate_hint(self, question: str) -> str:
        return self.interviewer.generate_hint(question)

    def generate_hint_stream(self, question: str):
        yield from self.interviewer.generate_hint_stream(question)

    def generate_report(
        self, questions: list[str], answers: list[str], scores: list[str],
    ) -> str:
        self._status = "reporting"
        report = self.report_writer.generate_summary(
            questions, answers, scores, profile=None,
        )
        self._status = "completed"
        return report

    def get_agent_log(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._agent_log[-limit:]

    def persist_memory(self, session_id: int) -> None:
        from backend.db.database import save_memory_data
        try:
            save_memory_data(session_id, self.shared_memory.to_dict())
        except Exception as exc:
            _log.warning("memory persist failed: %s", exc)

    def load_memory(self, session_id: int) -> None:
        from backend.db.database import load_memory_data
        try:
            data = load_memory_data(session_id)
            if data:
                self.shared_memory.load_dict(data)
        except Exception as exc:
            _log.warning("memory load failed: %s", exc)

    def get_shared_memory_snapshot(self) -> dict[str, Any]:
        snap: dict[str, Any] = {}
        for key in self.shared_memory.keys():
            entry = self.shared_memory.get_entry(key)
            if entry is None:
                continue
            val = entry.value
            if isinstance(val, str):
                snap[key] = val[:100] + ("..." if len(val) > 100 else "")
            elif isinstance(val, list):
                snap[key] = f"[{', '.join(str(v)[:40] for v in val[:5])}{'...' if len(val) > 5 else ''}]"
            elif isinstance(val, dict):
                snap[key] = f"{{{', '.join(f'{k}: {v}' for k, v in list(val.items())[:5])}}}"
            else:
                snap[key] = str(val)
        return snap

    def save_interview_report(
        self, session_id: str, user: str, topic: str,
        history: list[dict[str, str]],
    ) -> str | None:
        if not history:
            return None
        from backend.db.database import save_report as _save_report
        ai_summary = None
        try:
            questions = [h["q"] for h in history]
            answers = [h["a"] for h in history]
            scores = [h.get("score", "") for h in history]
            ai_summary = self.generate_report(questions, answers, scores)
        except Exception as exc:
            _log.warning("AI summary failed for session %s: %s", session_id, exc)
        try:
            _save_report(session_id, user, topic, ai_summary or "")
        except Exception as exc:
            _log.warning("failed to save report: %s", exc)
            return None
        return ai_summary

    def reset(self) -> None:
        self.shared_memory.clear()
        self.message_bus = MessageBus(max_history=500)
        self.telemetry = TelemetryCollector(max_traces=500)
        self._setup_subscriptions()
        self._agent_log.clear()
        self._status = "idle"
        self._followup_count = 0
        _log.info("orchestrator reset — memory, bus & telemetry cleared")
