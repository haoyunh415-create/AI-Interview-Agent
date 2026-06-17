"""API routes for per-session report history."""

import contextlib
import json
from collections import defaultdict
from statistics import mean
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.db.database import list_report_sessions, load_report, load_user_session_data
from core.constants import STAGES

router = APIRouter()


class SessionListItem(BaseModel):
    id: int
    session_id: str
    topic: str
    created_at: str | None


class SessionListResponse(BaseModel):
    sessions: list[SessionListItem]


class SessionReportResponse(BaseModel):
    session_id: str
    topic: str
    created_at: str
    ai_summary: str | None = None
    stats: dict[str, Any] | None = None
    stage_breakdown: list[dict[str, Any]] | None = None


def _parse_score(raw: str | None) -> dict[str, float] | None:
    if not raw:
        return None
    try:
        d = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(d, dict):
            return None
        return {k: float(v) for k, v in d.items() if isinstance(v, (int, float))}
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _get_row_col(row: Any, key: str, default: Any = None) -> Any:
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def _compute_per_stage_breakdown(data: list[Any]) -> list[dict[str, Any]]:
    stages: dict[str, list[Any]] = defaultdict(list)
    for row in data:
        stage = row["stage"] or "閫氱敤"
        stages[stage].append(row)

    result = []
    for stage_name in STAGES:
        if stage_name not in stages:
            continue
        rows = stages[stage_name]
        answered = [r for r in rows if _get_row_col(r, "status", "answered") == "answered"]
        skipped = [r for r in rows if _get_row_col(r, "status", "answered") == "skipped"]

        score_avg = None
        if answered:
            scores = []
            for r in answered:
                parsed = _parse_score(r["score"])
                if parsed:
                    scores.append(mean(parsed.values()) * 10)
            if scores:
                score_avg = round(mean(scores), 1)

        result.append(
            {
                "stage": stage_name,
                "total": len(rows),
                "answered_count": len(answered),
                "skipped_count": len(skipped),
                "score": score_avg,
                "questions": [r["question"] for r in answered],
                "answers": [r["answer"] for r in answered],
                "answers_summary": [
                    r["answer"][:120] + "..." if len(r["answer"]) > 120 else r["answer"] for r in answered
                ],
                "scores": [r["score"] for r in answered],
                "skipped_questions": [r["question"] for r in skipped],
            }
        )
    return result


@router.get("/reports", response_model=SessionListResponse)
def list_reports(user: str = "guest", limit: int = 20):
    """List all interview sessions with saved reports, newest first."""
    user = (user or "guest").strip() or "guest"
    rows = list_report_sessions(user, limit)
    return SessionListResponse(
        sessions=[
            SessionListItem(
                id=r["id"],
                session_id=r["session_id"],
                topic=r["topic"],
                created_at=r["created_at"],
            )
            for r in rows
        ]
    )


@router.get("/reports/{session_id}", response_model=SessionReportResponse)
def get_session_report(session_id: str, user: str = "guest"):
    """Get a full report for a specific interview session."""
    user = (user or "guest").strip() or "guest"
    report = load_report(session_id, user)
    if not report:
        raise HTTPException(404, "Report not found")

    data = load_user_session_data(session_id, user)
    stage_breakdown = _compute_per_stage_breakdown(data) if data else None

    ai_summary = None
    with contextlib.suppress(KeyError, IndexError, TypeError):
        ai_summary = report["ai_summary"]

    return SessionReportResponse(
        session_id=report["session_id"],
        topic=report["topic"],
        created_at=report["created_at"],
        ai_summary=ai_summary,
        stats={
            "total_questions": len(data),
            "answered_count": sum(s["answered_count"] for s in (stage_breakdown or [])),
            "skipped_count": sum(s["skipped_count"] for s in (stage_breakdown or [])),
        },
        stage_breakdown=stage_breakdown,
    )
