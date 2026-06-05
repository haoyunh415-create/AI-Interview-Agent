"""Resume analysis agent — extracts structured profile from resume text.

Publishes the profile to SharedMemory and emits ``resume.analyzed`` on
the message bus so Interviewer / Evaluator / ReportWriter can consume it.
"""

from typing import Any

from agents.base import BaseAgent
from core.memory import Events
from core.prompts import RESUME_ANALYST_ROLE, RESUME_ANALYST_TEMPLATE

_FALLBACK: dict[str, Any] = {
    "tech_stack": [],
    "level": "未知",
    "domains": [],
    "gaps": [],
    "highlights": [],
    "years_of_experience": 0,
    "overall_score": 0,
    "strengths": [],
    "weaknesses": [],
    "learning_path": [],
    "recommended_topics": [],
    "keywords": [],
}


def _ensure_fields(profile: dict[str, Any]) -> dict[str, Any]:
    result = _FALLBACK.copy()
    result.update(profile)
    return result


class ResumeAnalyst(BaseAgent):
    """Analyzes candidate resume and produces structured profile."""

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
            name="resume_analyst",
            role=RESUME_ANALYST_ROLE,
            temperature=0.3,
            api_key=api_key,
            shared_memory=shared_memory,
            message_bus=message_bus,
            telemetry=telemetry,
            provider=provider,
            model=model,
        )

    def analyze(self, resume_text: str) -> dict[str, Any]:
        if not resume_text or not resume_text.strip():
            self.memory_set("resume.profile", _FALLBACK)
            return _FALLBACK.copy()

        prompt = RESUME_ANALYST_TEMPLATE.format(
            resume_text=resume_text[:2500]
        )
        raw_profile = self.invoke_json_safe(prompt, fallback=_FALLBACK)
        profile = _ensure_fields(raw_profile)

        if not profile.get("keywords"):
            profile["keywords"] = _derive_keywords_from_tech_stack(profile)

        self.memory_set("resume.profile", profile)
        self.memory_set("resume.level", profile.get("level", "未知"))
        self.memory_set("resume.tech_stack", profile.get("tech_stack", []))
        self.memory_set("resume.keywords", profile.get("keywords", []))
        self.publish_event(Events.RESUME_ANALYZED, {"profile": profile})

        return profile


def _derive_keywords_from_tech_stack(profile: dict[str, Any]) -> list[dict[str, float]]:
    seen: set[str] = set()
    keywords: list[dict[str, float]] = []
    for term in profile.get("tech_stack", []):
        t = term.strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            keywords.append({"term": t, "weight": round(0.9 - len(keywords) * 0.05, 2)})
    for domain in profile.get("domains", []):
        d = domain.strip()
        if d and d.lower() not in seen:
            seen.add(d.lower())
            keywords.append({"term": d, "weight": round(0.75 - len(keywords) * 0.05, 2)})
    return keywords[:8]
