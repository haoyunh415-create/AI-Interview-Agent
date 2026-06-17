"""Report Writer agent — generates structured interview summary reports.
Publishes the report to SharedMemory and emits ``report.generated`` on the bus.
"""

from typing import Any

from agents.base import BaseAgent
from core.memory import Events
from core.prompts import REPORT_WRITER_ROLE, REPORT_WRITER_TEMPLATE


class ReportWriter(BaseAgent):
    """Generates interview summary reports."""

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
            name="report_writer",
            role=REPORT_WRITER_ROLE,
            temperature=0.5,
            api_key=api_key,
            shared_memory=shared_memory,
            message_bus=message_bus,
            telemetry=telemetry,
            provider=provider,
            model=model,
        )

    def _build_summary_prompt(self, questions, answers, scores, profile=None):
        if not questions:
            return None

        profile_context = ""
        if profile and profile.get("tech_stack"):
            profile_context = (
                f"\n候选人背景：\n"
                f"- 级别：{profile.get('level', '未知')}\n"
                f"- 技术栈：{', '.join(profile.get('tech_stack', []))}\n"
                f"- 专长：{', '.join(profile.get('domains', []))}\n"
                f"- 项目亮点：{', '.join(profile.get('highlights', []))}\n"
            )

        stages_lines = []
        for i, (q, a, s) in enumerate(zip(questions, answers, scores, strict=False), 1):
            stages_lines.append(f"### Q{i}: {q}\n回答: {a}\n评分: {s}\n")
        stages_data = "\n".join(stages_lines)

        return REPORT_WRITER_TEMPLATE.format(
            profile_context=profile_context,
            stages_data=stages_data,
        )

    def generate_summary(self, questions, answers, scores, profile=None):
        prompt = self._build_summary_prompt(questions, answers, scores, profile)
        if prompt is None:
            return "暂无面试记录"
        report = self.invoke(prompt)
        self._publish_report(report)
        return report

    def generate_summary_stream(self, questions, answers, scores, profile=None):
        prompt = self._build_summary_prompt(questions, answers, scores, profile)
        if prompt is None:
            yield "暂无面试记录"
            return
        yield from self.invoke_stream(prompt)

    def generate_final_report(self, history, profile=None):
        questions = [h.get("q", "") for h in history]
        answers = [h.get("a", "") for h in history]
        scores = [h.get("score", "无") for h in history]
        return self.generate_summary(questions, answers, scores, profile)

    def _publish_report(self, report: str) -> None:
        self.memory_set("report.latest", report)
        self.publish_event(
            Events.REPORT_GENERATED,
            {
                "report": report[:500],
            },
        )
