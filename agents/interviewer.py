"""Interviewer agent — generates interview questions.

Now reads candidate profile and knowledge context from SharedMemory (published
by ResumeAnalyst and KnowledgeRetriever), and publishes generated questions
to the message bus for traceability.
"""

from collections.abc import Iterator
from typing import Any

from agents.base import BaseAgent
from core.memory import Events
from core.prompts import (
    INTERVIEWER_FOLLOWUP_TEMPLATE,
    INTERVIEWER_HINT_TEMPLATE,
    INTERVIEWER_LEVEL_BIASES,
    INTERVIEWER_QUESTION_TEMPLATE,
    INTERVIEWER_ROLE,
)


def get_level_bias(profile: dict[str, Any] | None) -> str:
    """Return difficulty adjustment based on candidate level."""
    if not profile:
        return ""
    level = profile.get("level", "中级")
    return INTERVIEWER_LEVEL_BIASES.get(level, INTERVIEWER_LEVEL_BIASES["中级"])


class Interviewer(BaseAgent):
    """Generates interview questions based on topic, stage, and candidate profile."""

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
            name="interviewer",
            role=INTERVIEWER_ROLE,
            temperature=0.8,
            api_key=api_key,
            shared_memory=shared_memory,
            message_bus=message_bus,
            telemetry=telemetry,
            provider=provider,
            model=model,
        )

    def _resolve_profile(self, profile: dict[str, Any] | None) -> dict[str, Any] | None:
        if profile is not None:
            return profile
        return self.memory_get("resume.profile", None)

    def _resolve_context(self, topic: str, context: str = "") -> str:
        if context:
            return context
        return self.memory_get(f"context.{topic}", "")

    def generate_question(
        self,
        topic: str,
        stage: str,
        context: str = "",
        history: list[dict[str, str]] | None = None,
        profile: dict[str, Any] | None = None,
        custom_questions: list[str] | None = None,
    ) -> str:
        if custom_questions and history:
            idx = len(history)
            if idx < len(custom_questions):
                return custom_questions[idx]

        resolved_profile = self._resolve_profile(profile)
        resolved_context = self._resolve_context(topic, context)
        prompt = self._build_question_prompt(
            topic,
            stage,
            resolved_context,
            history,
            resolved_profile,
        )
        question = self.invoke(prompt)
        self._publish_question(question, stage, is_followup=False)
        return question

    def generate_question_stream(
        self,
        topic: str,
        stage: str,
        context: str = "",
        history: list[dict[str, str]] | None = None,
        profile: dict[str, Any] | None = None,
        custom_questions: list[str] | None = None,
    ) -> Iterator[str]:
        if custom_questions and history:
            idx = len(history)
            if idx < len(custom_questions):
                yield custom_questions[idx]
                return

        resolved_profile = self._resolve_profile(profile)
        resolved_context = self._resolve_context(topic, context)
        prompt = self._build_question_prompt(
            topic,
            stage,
            resolved_context,
            history,
            resolved_profile,
        )
        yield from self.invoke_stream(prompt)

    def _build_question_prompt(
        self,
        topic: str,
        stage: str,
        context: str,
        history: list[dict[str, str]] | None,
        profile: dict[str, Any] | None,
    ) -> str:
        history_context = ""
        if history:
            history_context = "\n已问过的问题：\n" + "\n".join("- " + h["q"] for h in history[-3:])

        profile_context = ""
        level_bias = ""
        if profile and profile.get("tech_stack"):
            profile_context = (
                f"\n候选人背景：\n"
                f"- 级别：{profile.get('level', '未知')}\n"
                f"- 技术栈：{', '.join(profile.get('tech_stack', []))}\n"
                f"- 专长：{', '.join(profile.get('domains', []))}\n"
            )
            level_bias = get_level_bias(profile)

        keyword_context = self._build_keyword_context(profile)

        return INTERVIEWER_QUESTION_TEMPLATE.format(
            topic=topic,
            stage=stage,
            context=context,
            history_context=history_context,
            profile_context=profile_context,
            keyword_context=keyword_context,
            level_bias=level_bias,
        )

    def _build_keyword_context(self, profile: dict[str, Any] | None) -> str:
        keywords = self.memory_get("resume.keywords", None)
        if not keywords:
            return ""
        terms = []
        for kw in keywords[:6]:
            term = kw.get("term", "")
            weight = kw.get("weight", 0.5)
            if term:
                label = "核心" if weight >= 0.7 else "补充"
                terms.append(f"  - {term} [{label}]")
        if not terms:
            return ""
        return "\n候选人核心技术关键词（优先考察高权重的关键词）：\n" + "\n".join(terms)

    def generate_followup(
        self,
        original_question: str,
        answer: str,
        evaluation: dict[str, Any],
        stage: str,
    ) -> str:
        prompt = self._build_followup_prompt(original_question, answer, evaluation, stage)
        question = self.invoke(prompt, temperature=0.6)
        self._publish_question(question, stage, is_followup=True)
        return question

    def generate_followup_stream(
        self,
        original_question: str,
        answer: str,
        evaluation: dict[str, Any],
        stage: str,
    ) -> Iterator[str]:
        prompt = self._build_followup_prompt(original_question, answer, evaluation, stage)
        yield from self.invoke_stream(prompt, temperature=0.6)

    def _build_followup_prompt(
        self,
        original_question: str,
        answer: str,
        evaluation: dict[str, Any],
        stage: str,
    ) -> str:
        followup_reason = evaluation.get("followup_reason", "回答不够深入")
        weakness_summary = evaluation.get("summary", "")
        return INTERVIEWER_FOLLOWUP_TEMPLATE.format(
            original_question=original_question,
            answer=answer,
            weakness_summary=weakness_summary,
            followup_reason=followup_reason,
            stage=stage,
        )

    def generate_hint(self, question: str) -> str:
        prompt = self._build_hint_prompt(question)
        return self.invoke(prompt, temperature=0.3)

    def generate_hint_stream(self, question: str) -> Iterator[str]:
        prompt = self._build_hint_prompt(question)
        yield from self.invoke_stream(prompt, temperature=0.3)

    def _build_hint_prompt(self, question: str) -> str:
        return INTERVIEWER_HINT_TEMPLATE.format(question=question)

    def _publish_question(self, question: str, stage: str, is_followup: bool) -> None:
        event_type = Events.FOLLOWUP_GENERATED if is_followup else Events.QUESTION_GENERATED
        self.publish_event(
            event_type,
            {
                "question": question,
                "stage": stage,
                "is_followup": is_followup,
            },
        )
