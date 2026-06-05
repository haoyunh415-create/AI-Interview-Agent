"""API routes for mock interview mode."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.limiter import limiter
from backend.session_store import create_session, get_api_key, get_interview_state, get_orchestrator
from core.api_key import resolve_api_key
from core.config import MAX_FOLLOWUPS_PER_STAGE, RATE_LIMIT_LLM
from core.constants import STAGES, TOPIC_MAP
from core.logging_config import get_logger

_log = get_logger("api.interview")
router = APIRouter()


# 鈹€鈹€ Request / Response models 鈹€鈹€


class StartRequest(BaseModel):
    api_key: str = ""
    topic: str
    resume_text: str = ""
    custom_questions: list[str] | None = None
    provider: str | None = None
    model: str | None = None


class StartResponse(BaseModel):
    session_id: str
    question: str
    stage: str
    stage_index: int
    total_stages: int
    is_followup: bool


class AnswerRequest(BaseModel):
    session_id: str
    answer: str


class AnswerResponse(BaseModel):
    score_text: str
    score_json: dict[str, Any]
    needs_followup: bool
    is_followup: bool
    next_question: str | None
    stage_index: int
    completed: bool
    has_error: bool


class HintRequest(BaseModel):
    session_id: str


class HintResponse(BaseModel):
    hint: str


class ReportRequest(BaseModel):
    session_id: str


class ReportResponse(BaseModel):
    report: str


# 鈹€鈹€ Interview state is managed in session_store.py 鈹€鈹€
# Use get_interview_state(session_id) to access per-session state.
# This was previously a module-level _interview_state dict that caused
# dual-state bugs with session_store.py.


# 鈹€鈹€ Routes 鈹€鈹€


@router.post("/interview/start", response_model=StartResponse)
@limiter.limit(RATE_LIMIT_LLM)
async def start_interview(req: StartRequest, request: Request) -> StartResponse:
    effective_key = resolve_api_key(req.api_key)
    session_id = create_session(effective_key, provider=req.provider, model=req.model)
    orch = get_orchestrator(session_id)
    if orch is None:
        raise HTTPException(500, "Failed to create session")

    state = get_interview_state(session_id)
    state["stage_index"] = 0
    state["history"] = []
    state["is_followup"] = False
    state["followup_count"] = 0
    state["custom_questions"] = req.custom_questions

    try:
        if req.resume_text.strip():
            # Run resume analysis in thread pool (sync LLM call)
            await asyncio.to_thread(orch.analyze_resume, req.resume_text)

        internal_topic = TOPIC_MAP.get(req.topic, req.topic)

        # Retrieve knowledge context (fast 鈥?sync, no LLM)
        await asyncio.to_thread(orch.retrieve_context, internal_topic)

        # Generate question (sync LLM call)
        stage = STAGES[0]
        question = await asyncio.to_thread(
            orch.generate_question,
            topic=internal_topic,
            stage_idx=0,
            history=[],
            custom_questions=req.custom_questions,
        )
        if not question:
            _log.error("Generated empty question on start (topic=%s)", internal_topic)
            raise HTTPException(500, "Failed to generate interview question 鈥?LLM returned empty response")

        state["current_q"] = question
        state["_topic"] = internal_topic

        return StartResponse(
            session_id=session_id,
            question=question,
            stage=stage,
            stage_index=0,
            total_stages=len(STAGES),
            is_followup=False,
        )
    except Exception as e:
        raise HTTPException(500, str(e)) from e

@router.post("/interview/answer", response_model=AnswerResponse)
async def submit_answer(req: AnswerRequest) -> AnswerResponse:
    orch = get_orchestrator(req.session_id)
    if orch is None:
        raise HTTPException(404, "Session not found")

    state = get_interview_state(req.session_id)
    current_q = state.get("current_q")
    if not current_q:
        raise HTTPException(400, "No active question")

    try:
        stored_topic = state.get("_topic", "Transformer鏍稿績鍘熺悊")

        # Evaluate answer (contains sync LLM calls 鈥?run in thread pool)
        score_json, report, needs_followup = await asyncio.to_thread(
            orch.evaluate_answer,
            "guest", stored_topic, current_q, req.answer,
            state["stage_index"], req.session_id,
        )

        # Record history
        state["history"].append({"q": current_q, "a": req.answer})

        completed = False
        next_question = None
        is_followup = False
        new_stage_index = state["stage_index"]

        if needs_followup and state["followup_count"] < MAX_FOLLOWUPS_PER_STAGE:
            # Generate followup (sync LLM call)
            next_question = await asyncio.to_thread(
                orch.generate_followup,
                original_question=current_q,
                answer=req.answer,
                evaluation=score_json,
                stage_idx=state["stage_index"],
            )
            is_followup = True
            state["followup_count"] += 1

        elif state["stage_index"] >= len(STAGES) - 1:
            completed = True

        else:
            # Next stage
            new_stage_index = state["stage_index"] + 1
            internal_topic = stored_topic
            next_question = await asyncio.to_thread(
                orch.generate_question,
                topic=internal_topic,
                stage_idx=new_stage_index,
                history=state["history"],
                custom_questions=state.get("custom_questions"),
            )

        # 鈹€鈹€ Guard: LLM produced empty question 鈫?mark as completed 鈹€鈹€
        if next_question is not None and not next_question.strip():
            _log.warning("LLM returned empty next_question for session=%s 鈥?marking interview as completed", req.session_id)
            completed = True
            next_question = None

        # Update state
        state["current_q"] = next_question
        state["is_followup"] = is_followup
        if not is_followup and not completed:
            state["stage_index"] = new_stage_index
            state["followup_count"] = 0

        # Auto-save report when interview completes
        if completed and state.get("history"):
            stored_topic = state.get("_topic", "Transformer鏍稿績鍘熺悊")
            await asyncio.to_thread(
                orch.save_interview_report,
                req.session_id, "guest", stored_topic, state["history"],
            )

        return AnswerResponse(
            score_text=report,
            score_json=score_json,
            needs_followup=needs_followup,
            is_followup=is_followup,
            next_question=next_question,
            stage_index=new_stage_index,
            completed=completed,
            has_error=score_json.get("_parse_error", False),
        )
    except Exception as e:
        raise HTTPException(500, str(e)) from e

@router.post("/interview/hint", response_model=HintResponse)
async def get_hint(req: HintRequest) -> HintResponse:
    orch = get_orchestrator(req.session_id)
    if orch is None:
        raise HTTPException(404, "Session not found")

    state = get_interview_state(req.session_id)
    current_q = state.get("current_q")
    if not current_q:
        raise HTTPException(400, "No active question")

    # Check cache
    cache = state.setdefault("hint_cache", {})
    if current_q in cache:
        return HintResponse(hint=cache[current_q])

    try:
        hint = await asyncio.to_thread(orch.generate_hint, current_q)
        cache[current_q] = hint
        return HintResponse(hint=hint)
    except Exception as e:
        raise HTTPException(500, str(e)) from e

@router.post("/interview/report", response_model=ReportResponse)
async def generate_report(req: ReportRequest) -> ReportResponse:
    orch = get_orchestrator(req.session_id)
    if orch is None:
        raise HTTPException(404, "Session not found")

    state = get_interview_state(req.session_id)
    history = state.get("history", [])

    if not history:
        raise HTTPException(400, "No interview history")

    try:
        questions = [h["q"] for h in history]
        answers = [h["a"] for h in history]
        scores = [h.get("score", "") for h in history]

        report = await asyncio.to_thread(
            orch.generate_report,
            questions=questions,
            answers=answers,
            scores=scores,
        )
        return ReportResponse(report=report)
    except Exception as e:
        raise HTTPException(500, str(e)) from e

# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# Session resume
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?


class ResumeRequest(BaseModel):
    api_key: str = ""
    session_id: int  # DB session id
    resume_text: str = ""


class ResumeResponse(BaseModel):
    session_id: str  # in-memory session id
    question: str | None
    stage: str
    stage_index: int
    total_stages: int
    is_followup: bool
    history: list[dict[str, str]]
    completed: bool


@router.post("/interview/resume", response_model=ResumeResponse)
async def resume_interview(req: ResumeRequest) -> ResumeResponse:
    """Resume a previously saved interview session from the database."""
    from backend.db.database import load_session

    row = load_session(req.session_id)
    if row is None:
        raise HTTPException(404, "Session not found")

    # Create a new in-memory session
    effective_key = resolve_api_key(req.api_key)
    memory_session_id = create_session(effective_key)
    orch = get_orchestrator(memory_session_id)
    if orch is None:
        raise HTTPException(500, "Failed to create session")

    # Restore shared memory from persisted data
    orch.load_memory(req.session_id)

    # Parse history and state
    try:
        import json
        history = json.loads(row["history"]) if isinstance(row["history"], str) else []
    except (json.JSONDecodeError, TypeError):
        history = []

    stage_index = row["stage_index"]
    custom_questions = None
    try:
        raw = row["custom_questions"]
        if raw:
            custom_questions = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        pass

    # Analyze resume if provided (sync LLM call)
    if req.resume_text.strip():
        await asyncio.to_thread(orch.analyze_resume, req.resume_text)

    # Generate next question or resume from where we left off
    if not history:
        question = await asyncio.to_thread(
            orch.generate_question,
            topic=row["topic"],
            stage_idx=0,
            history=[],
            custom_questions=custom_questions,
        )
        stage_index = 0
    else:
        question = await asyncio.to_thread(
            orch.generate_question,
            topic=row["topic"],
            stage_idx=stage_index,
            history=history,
            custom_questions=custom_questions,
        )

    # Store state for subsequent API calls
    state = get_interview_state(memory_session_id)
    state["stage_index"] = stage_index
    state["history"] = history
    state["current_q"] = question
    state["is_followup"] = False
    state["followup_count"] = 0
    state["custom_questions"] = custom_questions
    state["_topic"] = row["topic"]

    stage = STAGES[stage_index] if stage_index < len(STAGES) else STAGES[-1]

    return ResumeResponse(
        session_id=memory_session_id,
        question=question,
        stage=stage,
        stage_index=stage_index,
        total_stages=len(STAGES),
        is_followup=False,
        history=history,
        completed=False,
    )


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
# Streaming evaluation via SSE
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?


@router.post("/interview/answer/stream")
def submit_answer_stream(req: AnswerRequest):
    """Streaming evaluation 鈥?returns SSE events.

    Events:
      ``{"type":"token","content":"..."}`` 鈥?real-time score text
      ``{"type":"done","score_text":"...","score_json":{...},"next_question":"...",
          "is_followup":bool,"stage_index":int,"completed":bool,"has_error":bool}``
    """
    orch = get_orchestrator(req.session_id)
    if orch is None:
        raise HTTPException(404, "Session not found")

    state = get_interview_state(req.session_id)
    current_q = state.get("current_q")
    if not current_q:
        raise HTTPException(400, "No active question")

    stored_topic = state.get("_topic", "Transformer鏍稿績鍘熺悊")
    stage_idx = state["stage_index"]

    def event_stream():
        collected_eval = ""

        # 鈹€鈹€ Phase 1: Stream evaluation 鈹€鈹€
        try:
            for chunk in orch.evaluate_answer_stream(
                user="guest",
                topic=stored_topic,
                question=current_q,
                answer=req.answer,
                stage_idx=stage_idx,
                session_id=req.session_id,
            ):
                collected_eval += chunk
                yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"
            return

        # 鈹€鈹€ Phase 2: Retrieve scores 鈹€鈹€
        score_json = orch.shared_memory.get("eval.latest", {})
        report = orch.shared_memory.get("eval.formatted", "")
        if not report:
            report = orch.evaluator.format_report(score_json)

        # Record history
        state["history"].append({"q": current_q, "a": req.answer})

        # 鈹€鈹€ Phase 3: Determine next action 鈹€鈹€
        needs_followup = orch.evaluator.should_followup(score_json)
        completed = False
        next_question = None
        is_followup = False
        new_stage_index = stage_idx

        if needs_followup and state["followup_count"] < MAX_FOLLOWUPS_PER_STAGE:
            # Generate followup question
            followup_stream = orch.generate_followup_stream(
                original_question=current_q,
                answer=req.answer,
                evaluation=score_json,
                stage_idx=stage_idx,
            )
            next_question = "".join(list(followup_stream))
            is_followup = True
            state["followup_count"] += 1

        elif stage_idx >= len(STAGES) - 1:
            completed = True

        else:
            # Advance to next stage
            new_stage_index = stage_idx + 1
            next_stream = orch.generate_question_stream(
                topic=stored_topic,
                stage_idx=new_stage_index,
                history=state["history"],
                custom_questions=state.get("custom_questions"),
            )
            next_question = "".join(list(next_stream))

        # 鈹€鈹€ Guard: LLM produced empty next_question 鈫?mark as completed 鈹€鈹€
        if next_question is not None and not next_question.strip():
            _log.warning("LLM returned empty next_question for session=%s 鈥?marking interview as completed (stream)", req.session_id)
            completed = True
            next_question = None

        # 鈹€鈹€ Phase 4: Update state 鈹€鈹€
        state["current_q"] = next_question
        state["is_followup"] = is_followup
        if not is_followup and not completed:
            state["stage_index"] = new_stage_index
            state["followup_count"] = 0

        # Auto-save report when interview completes (sync 鈥?must save before
        # "done" event so the report page can load it immediately)
        if completed and state.get("history"):
            try:
                orch.save_interview_report(
                    req.session_id, "guest", stored_topic, state["history"],
                )
            except Exception as exc:
                import traceback
                _log.error("Failed to save interview report: %s\n%s", exc, traceback.format_exc())

        # 鈹€鈹€ Phase 5: Send done event 鈹€鈹€
        done_data = json.dumps({
            "type": "done",
            "score_text": report,
            "score_json": score_json,
            "needs_followup": needs_followup,
            "is_followup": is_followup,
            "next_question": next_question,
            "stage_index": new_stage_index,
            "completed": completed,
            "has_error": score_json.get("_parse_error", False),
        }, ensure_ascii=False)
        yield f"data: {done_data}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
