import time
from db.database import save
from agents.resume_analyst import ResumeAnalyst
from agents.interviewer import Interviewer, get_level_bias
from agents.evaluator import Evaluator, MAX_FOLLOWUPS_PER_STAGE
from agents.knowledge_retriever import KnowledgeRetriever
from agents.report_writer import ReportWriter
from core.logging_config import get_logger, log_duration

STAGES = ["基础", "原理", "进阶", "项目", "挑战"]
_log = get_logger("orchestrator")


class InterviewOrchestrator:
    """Coordinates all agents through the interview lifecycle.

    Flow per stage:
    1. Interviewer generates main question
    2. User answers
    3. Evaluator scores + decides if followup needed
    4a. If followup needed → Interviewer generates followup (repeat up to 3x)
    4b. If no followup → advance to next stage
    5. After all stages → ReportWriter generates summary
    """

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.resume_analyst = ResumeAnalyst(api_key)
        self.interviewer = Interviewer(api_key)
        self.evaluator = Evaluator(api_key)
        self.knowledge_retriever = KnowledgeRetriever(api_key)
        self.report_writer = ReportWriter(api_key)

        self._profile = None
        self._context = ""
        self._status = "idle"
        self._followup_count = 0

    # ── Agent status for UI ──
    def agent_status(self):
        """Return list of agent names and their states."""
        return [
            ("简历分析师", "ready" if self._profile else "待分析"),
            ("知识检索官", "ready" if self._context else "待检索"),
            ("面试官", "ready" if self._status in ("questioning", "scored", "followup") else "等待中"),
            ("评价官", "ready" if self._status == "evaluating" else "等待中"),
            ("报告生成官", "ready" if self._status == "completed" else "等待中"),
        ]

    @property
    def followup_count(self):
        return self._followup_count

    # ── Resume analysis ──
    def analyze_resume(self, resume_text):
        if resume_text and resume_text.strip():
            self._profile = self.resume_analyst.analyze(resume_text)
        else:
            self._profile = None
        return self._profile

    # ── Knowledge retrieval ──
    def fetch_context(self, topic):
        self._context = self.knowledge_retriever.get_topic_context(topic)
        return self._context

    # ── Question generation ──
    def generate_question(self, topic, stage_idx, history=None, custom_questions=None):
        """Generate the main question for a stage. Resets followup counter."""
        self._followup_count = 0
        stage = STAGES[stage_idx]
        self._status = "questioning"

        question = self.interviewer.generate_question(
            topic=topic,
            stage=stage,
            context=self._context,
            history=history,
            profile=self._profile,
            custom_questions=custom_questions,
        )
        return question

    def generate_followup(self, original_question, answer, evaluation, stage_idx):
        """Generate a follow-up question based on the previous answer."""
        stage = STAGES[stage_idx]
        self._status = "followup"
        self._followup_count += 1

        question = self.interviewer.generate_followup(
            original_question=original_question,
            answer=answer,
            evaluation=evaluation,
            stage=stage,
        )
        return question

    # ── Answer evaluation ──
    def evaluate_answer(self, user, topic, question, answer, stage_idx):
        """Evaluate answer and decide whether to follow up or move on."""
        stage = STAGES[stage_idx]
        self._status = "evaluating"
        t0 = time.monotonic()

        score_json = self.evaluator.evaluate(
            question, answer, stage, self._followup_count
        )
        save(user, topic, question, answer, score_json, stage)

        needs_followup = self.evaluator.should_followup(score_json)
        log_duration(_log, f"evaluate stage={stage} followup={needs_followup}", t0)

        report = self.evaluator.format_report(score_json)
        self._status = "scored"
        return score_json, report, needs_followup

    # ── Streaming question generation ──
    def generate_question_stream(self, topic, stage_idx, history=None, custom_questions=None):
        """Stream question generation. Resets followup counter."""
        self._followup_count = 0
        stage = STAGES[stage_idx]
        self._status = "questioning"
        yield from self.interviewer.generate_question_stream(
            topic=topic,
            stage=stage,
            context=self._context,
            history=history,
            profile=self._profile,
            custom_questions=custom_questions,
        )

    def generate_followup_stream(self, original_question, answer, evaluation, stage_idx):
        """Stream follow-up question generation."""
        stage = STAGES[stage_idx]
        self._status = "followup"
        self._followup_count += 1
        yield from self.interviewer.generate_followup_stream(
            original_question=original_question,
            answer=answer,
            evaluation=evaluation,
            stage=stage,
        )

    # ── Hint generation ──
    def generate_hint(self, question):
        return self.interviewer.generate_hint(question)

    def generate_hint_stream(self, question):
        yield from self.interviewer.generate_hint_stream(question)

    # ── Final report ──
    def generate_report(self, questions, answers, scores):
        self._status = "reporting"
        report = self.report_writer.generate_summary(
            questions, answers, scores, self._profile
        )
        self._status = "completed"
        return report

    # ── Convenience: full step (backward compat) ──
    def step(
        self,
        user,
        topic,
        stage_idx,
        question=None,
        answer=None,
        history=None,
        resume=None,
        custom_questions=None,
    ):
        """Single step interface. Returns a dict with interview state.

        Dict keys when answer is None (starting):
            {"question": str, "stage_idx": int, "is_followup": False}

        Dict keys when answer is given:
            {"report": str, "next_q": str, "next_idx": int,
             "is_followup": bool, "stage_completed": bool,
             "all_completed": bool, "score_json": dict}
        """
        if resume:
            self.analyze_resume(resume)
        if not self._context:
            self.fetch_context(topic)

        if answer is None:
            q = self.generate_question(topic, stage_idx, history, custom_questions)
            return {
                "question": q,
                "stage_idx": stage_idx,
                "is_followup": False,
            }

        score_json, report, needs_followup = self.evaluate_answer(
            user, topic, question, answer, stage_idx
        )

        if needs_followup and self._followup_count < MAX_FOLLOWUPS_PER_STAGE:
            followup_q = self.generate_followup(
                question, answer, score_json, stage_idx
            )
            return {
                "report": report,
                "next_q": followup_q,
                "next_idx": stage_idx,  # stay in same stage
                "is_followup": True,
                "stage_completed": False,
                "all_completed": False,
                "score_json": score_json,
            }

        # Move to next stage
        next_idx = min(stage_idx + 1, len(STAGES) - 1)
        all_completed = stage_idx >= len(STAGES) - 1

        if all_completed:
            return {
                "report": report,
                "next_q": None,
                "next_idx": next_idx,
                "is_followup": False,
                "stage_completed": True,
                "all_completed": True,
                "score_json": score_json,
            }

        next_q = self.generate_question(topic, next_idx, history, custom_questions)
        return {
            "report": report,
            "next_q": next_q,
            "next_idx": next_idx,
            "is_followup": False,
            "stage_completed": True,
            "all_completed": False,
            "score_json": score_json,
        }

    def reset(self):
        """Reset orchestrator state for a new interview."""
        self._profile = None
        self._context = ""
        self._status = "idle"
        self._followup_count = 0
