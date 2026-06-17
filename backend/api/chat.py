"""API routes for chat mode — streaming SSE, batch, and session-based."""

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.limiter import limiter
from backend.session_store import create_chat_session, get_chat_credentials
from core.api_key import resolve_api_key
from core.chat_context import auto_truncate_for_llm
from core.config import RATE_LIMIT_LLM
from core.llm import get_llm

router = APIRouter()

SYSTEM_PROMPT = "你是一个友好的 AI 助手。请用中文回答用户的问题。"


# ═════════════════════════════════════════════════════
# Schemas
# ═════════════════════════════════════════════════════


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    api_key: str = ""
    provider: str | None = None
    model: str | None = None
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


class ChatSessionRequest(BaseModel):
    api_key: str = ""
    provider: str | None = None
    model: str | None = None


class ChatSessionResponse(BaseModel):
    session_id: str


class ChatSessionMessageRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


def _build_messages(message: str, history: list[ChatMessage]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": message})
    return auto_truncate_for_llm(messages)


def _get_llm_and_reply(
    api_key: str,
    message: str,
    history: list[ChatMessage],
    provider: str | None = None,
    model: str | None = None,
) -> str:
    effective_key = resolve_api_key(api_key)
    llm = get_llm(effective_key, temperature=0.8, provider=provider, model=model)
    safe_messages = _build_messages(message, history)
    response = llm.invoke(safe_messages)
    return response.content


# ═════════════════════════════════════════════════════
# Batch endpoint (non-streaming — backward compatible)
# ═════════════════════════════════════════════════════


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(RATE_LIMIT_LLM)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    try:
        reply = await asyncio.to_thread(
            _get_llm_and_reply,
            req.api_key,
            req.message,
            req.history,
            req.provider,
            req.model,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(500, str(e)) from e


# ═════════════════════════════════════════════════════
# SSE streaming endpoint (chat)
# ═════════════════════════════════════════════════════


@router.post("/chat/stream")
@limiter.limit(RATE_LIMIT_LLM)
async def chat_stream(req: ChatRequest, request: Request):
    """SSE streaming chat.

    Events:
      ``{"type":"token","content":"..."}`` — each token
      ``{"type":"done"}`` — stream complete
      ``{"type":"error","message":"..."}`` — error

    Same interface as ``/chat`` but tokens arrive in real-time.
    """
    effective_key = resolve_api_key(req.api_key)
    provider = req.provider
    model = req.model

    def event_stream():
        llm = get_llm(effective_key, temperature=0.8, provider=provider, model=model)
        safe_messages = _build_messages(req.message, req.history)

        try:
            for chunk in llm.stream(safe_messages):
                if chunk.content:
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content}, ensure_ascii=False)}\n\n"
            yield 'data: {"type": "done"}\n\n'
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ═════════════════════════════════════════════════════
# Session-based chat
# ═════════════════════════════════════════════════════


@router.post("/chat/session", response_model=ChatSessionResponse)
@limiter.limit(RATE_LIMIT_LLM)
async def create_chat(req: ChatSessionRequest, request: Request) -> ChatSessionResponse:
    effective_key = resolve_api_key(req.api_key)
    session_id = create_chat_session(effective_key, provider=req.provider, model=req.model)
    return ChatSessionResponse(session_id=session_id)


@router.post("/chat/session/{session_id}", response_model=ChatResponse)
@limiter.limit(RATE_LIMIT_LLM)
async def chat_with_session(
    session_id: str,
    req: ChatSessionMessageRequest,
    request: Request,
) -> ChatResponse:
    creds = get_chat_credentials(session_id)
    if creds is None:
        raise HTTPException(404, "Chat session not found")

    try:
        reply = await asyncio.to_thread(
            _get_llm_and_reply,
            creds["api_key"],
            req.message,
            req.history,
            creds.get("provider"),
            creds.get("model"),
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(500, str(e)) from e
