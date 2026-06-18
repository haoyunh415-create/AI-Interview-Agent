"""API routes for reports."""

import asyncio
import json
import os
from collections import defaultdict
from statistics import mean
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents.report_writer import ReportWriter
from backend.db.database import load_user
from core.api_key import resolve_api_key
from core.constants import STAGES
from report.report_generator import generate_pdf

router = APIRouter()


class ReportRequest(BaseModel):
    api_key: str = ""
    user: str = "guest"


class ReportResponse(BaseModel):
    stats: dict[str, Any]
    questions: list[str]
    answers: list[str]
    scores: list[str]
    ai_summary: str | None = None


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


def _compute_topic_scores(data: list[Any]) -> dict[str, float]:
    topic_scores: dict[str, list[float]] = {}
    for row in data:
        topic = row["topic"] or "閫氱敤"
        parsed = _parse_score(row["score"])
        if parsed:
            avg = mean(parsed.values()) * 10
            topic_scores.setdefault(topic, []).append(avg)
    return {t: round(mean(v), 1) for t, v in topic_scores.items() if v}


def _compute_stage_scores(data: list[Any]) -> dict[str, float]:
    stage_scores: dict[str, list[float]] = {}
    for row in data:
        stage = row["stage"] or "閫氱敤"
        parsed = _parse_score(row["score"])
        if parsed:
            avg = mean(parsed.values()) * 10
            stage_scores.setdefault(stage, []).append(avg)
    return {s: round(mean(v), 1) for s, v in stage_scores.items() if v}


def _compute_correct_rate(data: list[Any]) -> int | None:
    scores = []
    for row in data:
        parsed = _parse_score(row["score"])
        if parsed and "correctness" in parsed:
            scores.append(parsed["correctness"])
    if not scores:
        return None
    return round(mean(scores) * 10)


def _get_row_col(row: Any, key: str, default: Any = None) -> Any:
    """Get a column from either a dict or sqlite3.Row."""
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def _compute_per_stage_breakdown(data: list[Any]) -> list[dict[str, Any]]:
    """Group rows by stage, compute per-stage stats, identify skipped."""
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
                "scores": [r["score"] for r in answered],
                "skipped_questions": [r["question"] for r in skipped],
            }
        )
    return result


def _format_stages_for_prompt(stages: list[dict[str, Any]]) -> str:
    """Format per-stage breakdown as text for the report writer prompt."""
    lines = []
    for s in stages:
        lines.append(f"\n[Stage {s['stage']}]")
        lines.append(f"Status: {s['answered_count']} answered, {s['skipped_count']} skipped")
        if s["score"] is not None:
            lines.append(f"Stage score: {s['score']}/100")
        if s["answered_count"] > 0:
            for q, a, sc in zip(s["questions"], s["answers"], s["scores"], strict=False):
                lines.append(f"  Q: {q}")
                lines.append(f"  A: {a[:200]}")
                lines.append(f"  璇勫垎: {sc}")
        if s["skipped_count"] > 0:
            for q in s["skipped_questions"]:
                lines.append(f"  鈴笍 [宸茶烦杩嘳 {q}")
    return "\n".join(lines)


@router.post("/report", response_model=ReportResponse)
async def get_report(req: ReportRequest) -> ReportResponse:
    data = load_user(req.user)
    if not data:
        raise HTTPException(404, "No interview records found")

    questions = [row["question"] for row in data]
    answers = [row["answer"] for row in data]
    scores = [row["score"] for row in data]

    topics = list({row["topic"] for row in data if row["topic"]})
    stages = list({row["stage"] for row in data if row["stage"]})

    # Per-stage breakdown
    stage_breakdown = _compute_per_stage_breakdown(data)

    # Stats with chart data
    stats = {
        "total_questions": len(questions),
        "topics_covered": len(topics),
        "stages_covered": len(stages),
        "total_stages": 5,
        "last_time": data[-1]["time"] if data else None,
        "correct_rate": _compute_correct_rate(data),
        "topic_scores": _compute_topic_scores(data),
        "stage_scores": _compute_stage_scores(data),
        "stage_breakdown": stage_breakdown,
        "skipped_count": sum(s["skipped_count"] for s in stage_breakdown),
        "answered_count": sum(s["answered_count"] for s in stage_breakdown),
    }

    # AI summary with per-stage data
    ai_summary = None
    effective_key = resolve_api_key(req.api_key)
    if effective_key and questions:
        try:
            writer = ReportWriter(effective_key)
            stages_text = _format_stages_for_prompt(stage_breakdown)
            summary = await asyncio.to_thread(
                writer.generate_summary,
                questions,
                answers,
                scores,
                stages_text=stages_text,
            )
            ai_summary = summary
        except Exception:
            ai_summary = None

    return ReportResponse(
        stats=stats,
        questions=questions,
        answers=answers,
        scores=scores,
        ai_summary=ai_summary,
    )


@router.post("/report/pdf")
def generate_report_pdf(req: ReportRequest) -> FileResponse:
    """Generate and download a PDF report."""
    data = load_user(req.user)
    if not data:
        raise HTTPException(404, "No interview records found")

    safe_user = "".join(ch for ch in (req.user or "guest") if ch.isalnum() or ch in ("-_."))
    safe_user = safe_user.replace("..", "").replace("\\", "").replace("/", "")
    safe_user = safe_user.strip("-_. ") or "guest"

    output_dir = os.path.abspath("outputs/reports")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{safe_user}_report.pdf")

    generate_pdf(data, pdf_path)

    if not os.path.isfile(pdf_path):
        raise HTTPException(500, f"PDF generation failed: {pdf_path}")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{safe_user}_report.pdf",
    )
