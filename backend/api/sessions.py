"""API routes for session management."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.db.database import delete_session, list_sessions

router = APIRouter()


class SessionItem(BaseModel):
    id: int
    topic: str
    stage_index: int
    question_count: int
    updated_at: str | None


class SessionListResponse(BaseModel):
    sessions: list[dict]


@router.get("/sessions", response_model=SessionListResponse)
def get_sessions(user: str = "guest", limit: int = 10) -> SessionListResponse:
    rows = list_sessions(user, limit=limit)
    result = []
    for row in rows:
        import json

        try:
            history = json.loads(row["history"]) if isinstance(row["history"], str) else []
        except (json.JSONDecodeError, TypeError):
            history = []
        result.append(
            {
                "id": row["id"],
                "topic": row["topic"],
                "stage_index": row["stage_index"],
                "question_count": len(history),
                "updated_at": row["updated_at"],
            }
        )
    return SessionListResponse(sessions=result)


@router.delete("/sessions/{session_id}")
def remove_session(session_id: int, user: str = "guest") -> dict:
    ok = delete_session(session_id, user)
    return {"ok": ok}


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Interview search
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
@router.get("/interviews/search")
def search_interviews(
    q: str,
    user: str = "guest",
    limit: int = 20,
) -> dict:
    """Full-text search across interview questions and answers."""
    from backend.db.database import search_interviews as db_search

    rows = db_search(q, user=user, limit=limit)
    results = []
    for row in rows:
        results.append(
            {
                "id": row["id"],
                "user": row["user"],
                "topic": row["topic"],
                "question": row["question"],
                "answer": row["answer"][:200] + ("..." if len(row["answer"]) > 200 else ""),
                "score": row["score"],
                "stage": row["stage"],
                "time": row["time"],
            }
        )
    return {"results": results, "total": len(results)}
