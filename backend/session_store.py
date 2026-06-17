"""In-memory session store for orchestrator instances and interview state.

Orchestrators are created on first request and cached by session_id.
Sessions expire after ``SESSION_TTL`` seconds (default 2 hours).

A background cleanup task (``start_cleanup_task``) periodically sweeps
expired sessions from both ``_store`` and ``_chat_sessions``.

Every session also holds a unified ``interview_state`` dict originally defined
in ``api/interview.py`` — consolidated here to avoid dual-state bugs.
"""

import asyncio
import time
import uuid
from typing import Any

from agents.orchestrator import InterviewOrchestrator
from core.logging_config import get_logger

_log = get_logger("session_store")

_store: dict[str, dict] = {}
_chat_sessions: dict[str, dict[str, Any]] = {}
SESSION_TTL = 7200  # 2 hours
_cleanup_interval = 600  # check every 10 minutes
_last_cleanup = time.monotonic()
_cleanup_task: asyncio.Task | None = None


def _make_default_state() -> dict[str, Any]:
    """Return a fresh interview-state dict (was module-level in api/interview.py)."""
    return {
        "stage_index": 0,
        "history": [],
        "current_q": None,
        "is_followup": False,
        "followup_count": 0,
        "custom_questions": None,
        "hint_cache": {},
        "_topic": "Transformer核心原理",
    }


def _cleanup() -> None:
    """Remove expired sessions from both ``_store`` and ``_chat_sessions``.

    Throttled to run at most once every ``_cleanup_interval`` seconds.
    Called on every ``create_session`` (hot path) and periodically via the
    background ``_cleanup_loop`` (cold path).
    """
    global _last_cleanup
    now = time.monotonic()
    if now - _last_cleanup < _cleanup_interval:
        return

    # Clean main interview sessions
    expired = [sid for sid, data in _store.items() if now - data["created_at"] > SESSION_TTL]
    for sid in expired:
        del _store[sid]

    # Clean lightweight chat sessions
    chat_expired = [sid for sid, data in _chat_sessions.items() if now - data.get("created_at", 0) > SESSION_TTL]
    for sid in chat_expired:
        del _chat_sessions[sid]

    total = len(expired) + len(chat_expired)
    if total:
        _log.info(
            "cleaned up %d expired session(s) (%d interview, %d chat), remaining: %d + %d",
            total,
            len(expired),
            len(chat_expired),
            len(_store),
            len(_chat_sessions),
        )
    _last_cleanup = now


async def _cleanup_loop() -> None:
    """Background loop: sweep expired sessions every ``_cleanup_interval`` seconds."""
    while True:
        await asyncio.sleep(_cleanup_interval)
        _cleanup()
        _log.debug("background cleanup tick — %d interview, %d chat sessions", len(_store), len(_chat_sessions))


def start_cleanup_task() -> None:
    """Start the background cleanup loop. Safe to call multiple times."""
    global _cleanup_task
    if _cleanup_task is not None and not _cleanup_task.done():
        return  # already running
    _cleanup_task = asyncio.create_task(_cleanup_loop())
    _log.info("background session cleanup task started (interval=%ds)", _cleanup_interval)


def stop_cleanup_task() -> None:
    """Cancel the background cleanup loop. Safe to call if not running."""
    global _cleanup_task
    if _cleanup_task is None or _cleanup_task.done():
        return
    _cleanup_task.cancel()
    _cleanup_task = None
    _log.info("background session cleanup task stopped")


def create_session(api_key: str | None = None, provider: str | None = None, model: str | None = None) -> str:
    """Create a new session and return its ID."""
    _cleanup()
    session_id = str(uuid.uuid4())[:8]
    orch = InterviewOrchestrator(api_key, provider=provider, model=model)
    _store[session_id] = {
        "orchestrator": orch,
        "api_key": api_key,
        "provider": provider,
        "model": model,
        "created_at": time.monotonic(),
        "metadata": {},
        "interview_state": _make_default_state(),
    }
    _log.info(
        "created session id=%s provider=%s model=%s (total active: %d)",
        session_id,
        provider or "(env)",
        model or "(env)",
        len(_store),
    )
    return session_id


def get_orchestrator(session_id: str) -> InterviewOrchestrator | None:
    """Get the orchestrator for a session."""
    data = _store.get(session_id)
    if data is None:
        return None
    return data["orchestrator"]


def get_interview_state(session_id: str) -> dict[str, Any] | None:
    """Get (or initialize) the interview-state dict for a session."""
    data = _store.get(session_id)
    if data is None:
        return None
    if "interview_state" not in data:
        data["interview_state"] = _make_default_state()
    return data["interview_state"]


def delete_session(session_id: str) -> None:
    """Delete a session."""
    _store.pop(session_id, None)
    _log.info("deleted session id=%s (total active: %d)", session_id, len(_store))


def get_api_key(session_id: str) -> str | None:
    """Get the API key for a session."""
    data = _store.get(session_id)
    if data is None:
        return None
    return data["api_key"]


def get_session_count() -> int:
    """Return the number of active sessions."""
    return len(_store)


def persist_all_sessions() -> int:
    """Persist all active interview sessions' state to a local JSON snapshot.

    Called during graceful shutdown so interview state survives a restart.
    The snapshot is loaded by ``restore_sessions()`` on next startup.

    Returns the number of sessions persisted.
    """
    if not _store:
        return 0

    import json

    snapshot: dict[str, dict[str, Any]] = {}
    for sid, data in _store.items():
        orch = data.get("orchestrator")
        interview_state = data.get("interview_state")
        if orch is None or interview_state is None:
            continue
        snapshot[sid] = {
            "api_key": data.get("api_key"),
            "provider": data.get("provider"),
            "model": data.get("model"),
            "created_at": data.get("created_at"),
            "interview_state": interview_state,
            "memory_snapshot": orch.get_shared_memory_snapshot(),
            "memory_dict": orch.shared_memory.to_dict(),
        }

    snapshot_path = _snapshot_path()
    try:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, default=str)
        _log.info("persisted %d session(s) to %s", len(snapshot), snapshot_path)
    except Exception as exc:
        _log.warning("failed to persist session snapshot: %s", exc)
        return 0
    return len(snapshot)


def restore_sessions() -> int:
    """Restore interview sessions from a previous shutdown snapshot.

    Returns the number of sessions restored.
    """
    snapshot_path = _snapshot_path()
    if not snapshot_path.exists():
        return 0

    import json

    try:
        with open(snapshot_path, encoding="utf-8") as f:
            snapshot = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        _log.warning("failed to restore session snapshot: %s", exc)
        return 0

    restored = 0
    for sid, data in snapshot.items():
        if sid in _store:
            continue
        orch = InterviewOrchestrator(
            api_key=data.get("api_key"),
            provider=data.get("provider"),
            model=data.get("model"),
        )
        memory_dict = data.get("memory_dict")
        if memory_dict:
            orch.shared_memory.load_dict(memory_dict)

        _store[sid] = {
            "orchestrator": orch,
            "api_key": data.get("api_key"),
            "provider": data.get("provider"),
            "model": data.get("model"),
            "created_at": data.get("created_at", 0),
            "metadata": {},
            "interview_state": data.get("interview_state", _make_default_state()),
        }
        restored += 1

    if restored:
        _log.info("restored %d session(s) from %s", restored, snapshot_path)
    return restored


def _snapshot_path():
    """Return the session snapshot file path."""
    from pathlib import Path

    from core.config import DATA_DIR

    return Path(DATA_DIR) / "sessions_snapshot.json"


# ═══════════════════════════════════════════════════════
# Chat Session Store — lightweight, no orchestrator
# ═══════════════════════════════════════════════════════


def create_chat_session(
    api_key: str,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """Create a lightweight chat session storing API credentials.

    Returns a session_id.  Use ``get_chat_credentials()`` to retrieve
    the stored credentials on subsequent requests.
    """
    session_id = str(uuid.uuid4())[:8]
    _chat_sessions[session_id] = {
        "api_key": api_key,
        "provider": provider,
        "model": model,
        "created_at": time.monotonic(),
    }
    _log.info("created chat session id=%s (total chat sessions: %d)", session_id, len(_chat_sessions))
    return session_id


def get_chat_credentials(session_id: str) -> dict[str, Any] | None:
    """Retrieve stored chat credentials by session_id.

    Returns ``{"api_key": str, "provider": str|None, "model": str|None}``
    or ``None`` if the session doesn't exist.
    """
    return _chat_sessions.get(session_id)


def delete_chat_session(session_id: str) -> bool:
    """Remove a chat session.  Returns ``True`` if it existed."""
    if session_id in _chat_sessions:
        del _chat_sessions[session_id]
        return True
    return False
