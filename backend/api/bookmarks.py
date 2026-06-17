"""API routes for bookmarks."""

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.db.database import (
    delete_bookmark,
    is_bookmarked,
    list_bookmarks,
    save_bookmark,
    update_bookmark_notes,
)

router = APIRouter()


class BookmarkCreate(BaseModel):
    user: str = "guest"
    question: str
    answer: str = ""
    topic: str = ""
    stage: str = ""
    notes: str = ""
    tags: list[str] | None = None


class BookmarkUpdate(BaseModel):
    user: str = "guest"
    notes: str


class BookmarkDelete(BaseModel):
    user: str = "guest"


class BookmarkItem(BaseModel):
    id: int
    question: str
    answer: str
    topic: str
    stage: str
    notes: str
    tags: list[str]
    created_at: str


class BookmarkListResponse(BaseModel):
    bookmarks: list[dict[str, Any]]


@router.post("/bookmarks", response_model=dict)
def create_bookmark(req: BookmarkCreate) -> dict:
    bm_id = save_bookmark(
        user=req.user,
        question=req.question,
        answer=req.answer,
        topic=req.topic,
        stage=req.stage,
        notes=req.notes,
        tags=req.tags,
    )
    return {"id": bm_id}


@router.get("/bookmarks", response_model=BookmarkListResponse)
def get_bookmarks(user: str = "guest", topic: str | None = None) -> BookmarkListResponse:
    rows = list_bookmarks(user, topic=topic)
    result = []
    for row in rows:
        try:
            tags = json.loads(row["tags"]) if isinstance(row["tags"], str) else row["tags"]
        except (json.JSONDecodeError, TypeError):
            tags = []
        result.append(
            {
                "id": row["id"],
                "question": row["question"],
                "answer": row["answer"] or "",
                "topic": row["topic"] or "",
                "stage": row["stage"] or "",
                "notes": row["notes"] or "",
                "tags": tags,
                "created_at": row["created_at"] or "",
            }
        )
    return BookmarkListResponse(bookmarks=result)


@router.delete("/bookmarks/{bookmark_id}", response_model=dict)
def remove_bookmark(bookmark_id: int, user: str = "guest") -> dict:
    ok = delete_bookmark(bookmark_id, user)
    if not ok:
        raise HTTPException(404, "Bookmark not found")
    return {"ok": True}


@router.get("/bookmarks/check", response_model=dict)
def check_bookmark(user: str = "guest", question: str = "") -> dict:
    return {"bookmarked": is_bookmarked(user, question)}


@router.put("/bookmarks/{bookmark_id}", response_model=dict)
def update_bookmark(bookmark_id: int, req: BookmarkUpdate) -> dict:
    """Update bookmark notes."""
    ok = update_bookmark_notes(bookmark_id, req.user, req.notes)
    if not ok:
        raise HTTPException(404, "Bookmark not found")
    return {"ok": True}
