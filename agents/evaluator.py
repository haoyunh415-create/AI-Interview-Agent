"""Evaluator agent — scores candidate answers with multi-dimensional analysis.

Reads knowledge context from SharedMemory (published by KnowledgeRetriever)
so it can reference authoritative material while grading.  Publishes scores
to the message bus for traceability and report generation.
"""

from collections.abc import Iterator
from typing import Any

from agents.base import BaseAgent
from core.config import MAX_FOLLOWUPS_PER_STAGE
from core.logging_config import get_logger
from core.memory import Events
from core.prompts import (
    EVALUATOR_ROLE,
    EVALUATOR_STAGE_EMPHASIS,
    EVALUATOR_TEMPLATE,
)

_log = get_logger("agent.evaluator")


# ═══════════════════════════════════════════════════════
# Well-known key for parse-error signalling
# ═══════════════════════════════════════════════════════

PARSE_ERROR_KEY = "_parse_error"


class Evaluator(BaseAgent):
    """Evaluates candidate answers with multi-dimensional scoring."""

    def __init__(
        self,
        api_key: str | None = None,
        shared_memory: Any = None,
        message_bus: Any = None,
        telemetry: Any = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__(
            name="evaluator",
            role=EVALUATOR_ROLE,
            temperature=0.0,
            api_key=api_key,
            shared_memory=shared_memory,
            message_bus=message_bus,
            telemetry=telemetry,
            provider=provider,
            model=model,
        )

    def evaluate(
        self,
        question: str,
        answer: str,
        stage: str,
        followup_count: int = 0,
        topic: str = "",
    ) -> dict[str, Any]:
        """Score an answer and return structured feedback including followup decision."""
        emphasis = EVALUATOR_STAGE_EMPHASIS.get(stage, "")

        followup_instruction = ""
        if followup_count >= MAX_FOLLOWUPS_PER_STAGE:
            followup_instruction = (
                "\n注意：本阶段追问次数已达上限，请设置 needs_followup 为 false。"
            )

        prompt = EVALUATOR_TEMPLATE.format(
            question=question,
            answer=answer,
            stage=stage,
            emphasis=emphasis,
            followup_instruction=followup_instruction,
        )
        # Evaluation must always be fresh — skip cache
        result = self.invoke_json(prompt, skip_cache=True)

        if followup_count >= MAX_FOLLOWUPS_PER_STAGE:
            result["needs_followup"] = False

        _log.info(
            "scores: correctness=%s logic=%s depth=%s expression=%s",
            result.get("correctness"),
            result.get("logic"),
            result.get("depth"),
            result.get("expression"),
        )

        self.memory_set("eval.latest", result, {"question": question, "stage": stage})
        self.publish_event(Events.ANSWER_EVALUATED, {
            "score": result,
            "question": question,
            "answer": answer,
            "stage": stage,
            "needs_followup": result.get("needs_followup", False),
        })

        return result

    def evaluate_stream(
        self,
        question: str,
        answer: str,
        stage: str,
        followup_count: int = 0,
        topic: str = "",
    ) -> Iterator[str]:
        """Streaming evaluation — yields progress messages, stores result in memory.

        After iteration completes, the result dict is available via
        ``self.memory_get("eval.latest")``.
        """
        emphasis = EVALUATOR_STAGE_EMPHASIS.get(stage, "")

        followup_instruction = ""
        if followup_count >= MAX_FOLLOWUPS_PER_STAGE:
            followup_instruction = (
                "\n注意：本阶段追问次数已达上限，请设置 needs_followup 为 false。"
            )

        yield "🔍 分析回答中...\n\n"

        prompt = EVALUATOR_TEMPLATE.format(
            question=question,
            answer=answer,
            stage=stage,
            emphasis=emphasis,
            followup_instruction=followup_instruction,
        )

        collected = ""
        for chunk in self.invoke_stream(prompt, skip_cache=True):
            collected += chunk
            yield chunk

        yield "\n\n📊 解析评分结果..."

        try:
            result = self._parse_json(collected)
        except ValueError:
            result = {
                "correctness": 0, "logic": 0, "depth": 0, "expression": 0,
                "summary": "评分解析失败",
                "improvement": "LLM 输出格式异常",
                "needs_followup": False, "followup_reason": "",
                PARSE_ERROR_KEY: True,
            }

        if followup_count >= MAX_FOLLOWUPS_PER_STAGE:
            result["needs_followup"] = False

        self.memory_set("eval.latest", result, {"question": question, "stage": stage})
        self.memory_set("eval.formatted", self.format_report(result), {"question": question})
        self.publish_event(Events.ANSWER_EVALUATED, {
            "score": result,
            "question": question,
            "answer": answer,
            "stage": stage,
            "needs_followup": result.get("needs_followup", False),
        })

        yield " ✅\n\n"
        yield self.format_report(result) + "\n"

    @staticmethod
    def should_followup(score_json: dict[str, Any]) -> bool:
        """Decide whether a follow-up is needed based on scores."""
        if not isinstance(score_json, dict):
            return False
        if score_json.get("needs_followup") is True:
            return True
        if score_json.get("needs_followup") is False:
            return False
        depth = score_json.get("depth", 10)
        correctness = score_json.get("correctness", 10)
        return depth < 5 or correctness < 5

    @staticmethod
    def format_report(score_json: dict[str, Any]) -> str:
        """Format score JSON into human-readable report string."""
        if not isinstance(score_json, dict):
            return str(score_json)
        s = score_json
        lines = [
            f"正确性: {s.get('correctness', '?')} | "
            f"逻辑: {s.get('logic', '?')} | "
            f"深度: {s.get('depth', '?')} | "
            f"表达: {s.get('expression', '?')}",
            "",
            f"点评: {s.get('summary', '无')}",
            "",
            f"改进建议: {s.get('improvement', '继续深化学习')}",
        ]
        if s.get("needs_followup"):
            lines.extend([
                "",
                f"追问原因: {s.get('followup_reason', '需要进一步考察')}",
            ])
        return "\n".join(lines)
