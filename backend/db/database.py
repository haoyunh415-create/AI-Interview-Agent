"""Database layer for interview records 鈥?supports SQLite and PostgreSQL.

Backend selection via ``DB_URL`` environment variable:
  - ``sqlite:///./data/interview.db`` 鈫?SQLite (default, for development)
  - ``postgresql://user:pass@host:5432/dbname`` 鈫?PostgreSQL (for production)

Uses a unified backend interface (``db/backend.py``) that converts ``?``
placeholders automatically.
"""

import contextlib
import json
import os
from datetime import datetime
from typing import Any

from core.config import DATA_DIR
from core.logging_config import get_logger

_log = get_logger("db")

DB_PATH = os.path.join(DATA_DIR, "interview.db")

# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Backend selection (delegates to db.backend)
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
_BACKEND = None  # cached per module reload


def _get_backend() -> Any:
    """Get the database backend (cached)."""
    global _BACKEND
    if _BACKEND is not None:
        try:
            _BACKEND.execute("SELECT 1")
            return _BACKEND
        except Exception:
            _BACKEND = None

    import backend.db.backend as _bk_mod

    _log.info("initializing database backend: %s", _bk_mod.DB_URL)
    _BACKEND = _bk_mod.get_backend()
    return _BACKEND


def set_db_path(path: str) -> None:
    """Override DB_PATH (used by tests for isolation).

    Also updates ``DB_URL`` in ``db/backend`` so the backend picks up
    the new path.
    """
    global DB_PATH
    DB_PATH = path
    # Also update the backend's DB_URL so it uses the new path
    from backend.db import backend as _backend_module

    _backend_module.DB_URL = f"sqlite:///{path}"
    # Reset BOTH caches - database._BACKEND and backend.db.backend._local.backend
    _reset_backend()
    _backend_module.reset_backend()


def _reset_backend() -> None:
    """Close and clear the cached backend."""
    global _BACKEND
    if _BACKEND is not None:
        with contextlib.suppress(Exception):
            _BACKEND.close()
        _BACKEND = None


def _column_names(table: str) -> set[str]:
    """Get column names for a table (uses PRAGMA for SQLite)."""
    backend = _get_backend()
    is_sqlite = not backend.__class__.__name__.startswith("Postgres")
    if is_sqlite:
        rows = backend.execute(f"PRAGMA table_info({table})")
        return {row["name"] for row in rows}
    # PostgreSQL 鈥?use information_schema
    rows = backend.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = ?",
        (table,),
    )
    return {row["column_name"] for row in rows}


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Initialization
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
def init_db() -> None:
    """Initialize the database schema.

    Uses ``CREATE TABLE IF NOT EXISTS`` so it's idempotent.
    For PostgreSQL, use Alembic migrations (``make db-migrate``).
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    backend = _get_backend()
    is_sqlite = not backend.__class__.__name__.startswith("Postgres")

    # 鈹€鈹€
    # SQLite-specific optimizations
    # 鈹€鈹€
    if is_sqlite:
        backend.execute("PRAGMA foreign_keys = ON")
        backend.execute("PRAGMA busy_timeout = 5000")
        backend.execute("PRAGMA journal_mode = WAL")
        backend.execute("PRAGMA synchronous = NORMAL")

    # 鈹€鈹€ Interviews table 鈹€鈹€
    backend.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL DEFAULT 'guest',
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            score TEXT,
            stage TEXT,
            time TEXT NOT NULL,
            created_at TEXT
        )
    """)

    columns = _column_names("interviews")
    if "created_at" not in columns:
        backend.execute("ALTER TABLE interviews ADD COLUMN created_at TEXT")
        if is_sqlite:
            backend.execute("UPDATE interviews SET created_at = COALESCE(time, datetime('now', 'localtime'))")
        else:
            backend.execute("UPDATE interviews SET created_at = COALESCE(time, NOW()::date)")

    backend.execute("""
        CREATE INDEX IF NOT EXISTS idx_interviews_user_time
        ON interviews(user, time, id)
    """)
    backend.execute("""
        CREATE INDEX IF NOT EXISTS idx_interviews_topic
        ON interviews(topic)
    """)
    backend.execute("""
        CREATE INDEX IF NOT EXISTS idx_interviews_stage
        ON interviews(stage)
    """)
    backend.execute("""
        CREATE INDEX IF NOT EXISTS idx_interviews_question
        ON interviews(question)
    """)

    # 鈹€鈹€ FTS5 full-text search (SQLite only) 鈹€鈹€
    if is_sqlite:
        _init_fts5(backend)

    # 鈹€鈹€ Sessions table 鈹€鈹€
    backend.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL DEFAULT 'guest',
            topic TEXT NOT NULL,
            stage_index INTEGER NOT NULL DEFAULT 0,
            history TEXT NOT NULL DEFAULT '[]',
            profile TEXT,
            context TEXT,
            custom_questions TEXT,
            followup_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'in_progress',
            memory_data TEXT DEFAULT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    backend.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_user_status
        ON sessions(user, status)
    """)
    backend.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_updated
        ON sessions(updated_at)
    """)

    # 鈹€鈹€ Migration: add memory_data column if upgrading 鈹€鈹€
    sess_columns = _column_names("sessions")
    if "memory_data" not in sess_columns:
        backend.execute("ALTER TABLE sessions ADD COLUMN memory_data TEXT DEFAULT NULL")
        _log.info("added memory_data column to sessions table")

    # 鈹€鈹€ Users table (auth) 鈹€鈹€
    backend.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    backend.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_username
        ON users(username)
    """)

    # 鈹€鈹€ Bookmarks table 鈹€鈹€
    backend.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL DEFAULT 'guest',
            question TEXT NOT NULL,
            answer TEXT DEFAULT '',
            topic TEXT DEFAULT '',
            stage TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            created_at TEXT NOT NULL
        )
    """)
    backend.execute("""
        CREATE INDEX IF NOT EXISTS idx_bookmarks_user
        ON bookmarks(user, created_at)
    """)

    # 鈹€鈹€ Reports table (per-session AI summaries) 鈹€鈹€
    backend.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user TEXT NOT NULL DEFAULT 'guest',
            topic TEXT NOT NULL,
            ai_summary TEXT,
            stats_json TEXT,
            created_at TEXT NOT NULL
        )
    """)
    backend.execute("""
        CREATE INDEX IF NOT EXISTS idx_reports_session
        ON reports(user, created_at DESC)
    """)


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# FTS5 Full-Text Search (SQLite only)
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
_FTS_ENABLED: bool = False


def _init_fts5(backend: Any) -> None:
    """Create FTS5 virtual table for full-text search on interviews."""
    global _FTS_ENABLED
    try:
        backend.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS interviews_fts USING fts5("
            "user, topic, question, answer, content='interviews', content_rowid='id')"
        )
        backend.execute_script("""
            CREATE TRIGGER IF NOT EXISTS interviews_ai AFTER INSERT ON interviews BEGIN
                INSERT INTO interviews_fts(rowid, user, topic, question, answer)
                VALUES (new.id, new.user, new.topic, new.question, new.answer);
            END;

            CREATE TRIGGER IF NOT EXISTS interviews_ad AFTER DELETE ON interviews BEGIN
                INSERT INTO interviews_fts(interviews_fts, rowid, user, topic, question, answer)
                VALUES ('delete', old.id, old.user, old.topic, old.question, old.answer);
            END;

            CREATE TRIGGER IF NOT EXISTS interviews_au AFTER UPDATE ON interviews BEGIN
                INSERT INTO interviews_fts(interviews_fts, rowid, user, topic, question, answer)
                VALUES ('delete', old.id, old.user, old.topic, old.question, old.answer);
                INSERT INTO interviews_fts(rowid, user, topic, question, answer)
                VALUES (new.id, new.user, new.topic, new.question, new.answer);
            END;
        """)
        backend.execute("""
            INSERT INTO interviews_fts(rowid, user, topic, question, answer)
            SELECT id, user, topic, question, answer FROM interviews
            WHERE id NOT IN (SELECT rowid FROM interviews_fts)
        """)
        _FTS_ENABLED = True
        _log.info("FTS5 full-text search enabled")
    except Exception as exc:
        if hasattr(backend, "_conn") and "fts5" in str(exc):
            _log.warning("FTS5 not available 鈥?falling back to LIKE search: %s", exc)
        else:
            _log.warning("FTS5 setup failed (non-fatal): %s", exc)


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# CRUD 鈥?Interviews
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
def _serialize_score(score: object) -> str:
    if isinstance(score, (dict, list)):
        return json.dumps(score, ensure_ascii=False)
    return "" if score is None else str(score)


def _first(rows: list[Any]) -> Any | None:
    """Return the first row from a result set, or ``None``."""
    return rows[0] if rows else None


def _ensure_column(backend: Any, table: str, column: str, definition: str) -> None:
    """Add a column to a table if it doesn't exist (idempotent migration)."""
    existing = _column_names(table)
    if column not in existing:
        backend.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        _log.info("added column %s.%s", table, column)


def save(
    user: str,
    topic: str,
    q: str,
    a: str,
    score: object,
    stage: str,
    status: str = "answered",
    session_id: str | None = None,
) -> None:
    """Save an interview record with status tracking.

    *status* can be ``"answered"``, ``"skipped"``, or ``"partial"``.
    *session_id* links this record to a specific interview session.
    """
    user = (user or "guest").strip() or "guest"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    backend = _get_backend()
    # Ensure status column exists (migration for existing DBs)
    _ensure_column(backend, "interviews", "status", "TEXT NOT NULL DEFAULT 'answered'")
    _ensure_column(backend, "interviews", "session_id", "TEXT DEFAULT NULL")
    backend.execute(
        "INSERT INTO interviews (user, topic, question, answer, score, stage, time, created_at, status, session_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user, topic, q, a, _serialize_score(score), stage, now, now, status, session_id),
    )


def load_user(user: str, limit: int | None = None) -> list[Any]:
    user = (user or "guest").strip() or "guest"
    query = """
        SELECT id, user, topic, question, answer, score, stage, time, created_at
        FROM interviews
        WHERE user = ?
        ORDER BY time ASC, id ASC
    """
    params: list[Any] = [user]
    if limit:
        query += " LIMIT ?"
        params.append(int(limit))
    return _get_backend().execute(query, params)


def load_user_stats(user: str) -> Any | None:
    user = (user or "guest").strip() or "guest"
    return _first(
        _get_backend().execute(
            """
        SELECT COUNT(*) AS total_questions, COUNT(DISTINCT topic) AS topics_covered,
               COUNT(DISTINCT stage) AS stages_covered, MAX(time) AS last_time
        FROM interviews WHERE user = ?
        """,
            (user,),
        )
    )


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Session persistence
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
def save_session(
    user: str,
    topic: str,
    stage_index: int,
    history: list[dict[str, str]],
    followup_count: int = 0,
    profile: dict[str, Any] | None = None,
    context: str | None = None,
    custom_questions: list[str] | None = None,
    session_id: int | None = None,
) -> int:
    user = (user or "guest").strip() or "guest"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_json = json.dumps(history, ensure_ascii=False)
    profile_json = json.dumps(profile, ensure_ascii=False) if profile else None
    custom_json = json.dumps(custom_questions, ensure_ascii=False) if custom_questions else None
    backend = _get_backend()

    if session_id is not None:
        backend.execute(
            "UPDATE sessions SET stage_index=?, history=?, profile=?, context=?, "
            "custom_questions=?, followup_count=?, updated_at=? WHERE id=? AND user=?",
            (stage_index, history_json, profile_json, context, custom_json, followup_count, now, session_id, user),
        )
        return session_id
    else:
        backend.execute(
            "INSERT INTO sessions (user, topic, stage_index, history, profile, context, "
            "custom_questions, followup_count, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)",
            (user, topic, stage_index, history_json, profile_json, context, custom_json, followup_count, now, now),
        )
        return backend.lastrowid  # type: ignore[return-value]


def load_session(session_id: int) -> Any | None:
    return _first(
        _get_backend().execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,),
        )
    )


def list_sessions(user: str, limit: int = 5) -> list[Any]:
    user = (user or "guest").strip() or "guest"
    return _get_backend().execute(
        "SELECT id, user, topic, stage_index, status, history, followup_count, "
        "created_at, updated_at FROM sessions WHERE user=? AND status='in_progress' "
        "ORDER BY updated_at DESC LIMIT ?",
        (user, limit),
    )


def delete_session(session_id: int, user: str) -> bool:
    user = (user or "guest").strip() or "guest"
    before = _get_backend().execute("SELECT 1 FROM sessions WHERE id=? AND user=?", (session_id, user))
    _get_backend().execute("DELETE FROM sessions WHERE id=? AND user=?", (session_id, user))
    after = _get_backend().execute("SELECT 1 FROM sessions WHERE id=? AND user=?", (session_id, user))
    return len(before) > 0 and len(after) == 0


def complete_session(session_id: int, user: str) -> bool:
    user = (user or "guest").strip() or "guest"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _get_backend().execute(
        "UPDATE sessions SET status='completed', updated_at=? WHERE id=? AND user=?",
        (now, session_id, user),
    )
    return True


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# SharedMemory persistence
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
def save_memory_data(session_id: int, memory_dict: dict[str, Any]) -> bool:
    serialized = json.dumps(memory_dict, ensure_ascii=False, default=str)
    _get_backend().execute(
        "UPDATE sessions SET memory_data=?, updated_at=datetime('now','localtime') WHERE id=?",
        (serialized, session_id),
    )
    return True


def load_memory_data(session_id: int) -> dict[str, Any] | None:
    row = _first(
        _get_backend().execute(
            "SELECT memory_data FROM sessions WHERE id=?",
            (session_id,),
        )
    )
    if row is None:
        return None
    raw = row["memory_data"]
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        _log.warning("failed to parse memory_data for session %s", session_id)
        return None


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Bookmark CRUD
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
def save_bookmark(
    user: str,
    question: str,
    answer: str = "",
    topic: str = "",
    stage: str = "",
    notes: str = "",
    tags: list[str] | None = None,
) -> int:
    user = (user or "guest").strip() or "guest"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tags_json = json.dumps(tags or [], ensure_ascii=False)
    backend = _get_backend()
    backend.execute(
        "INSERT INTO bookmarks (user, question, answer, topic, stage, notes, tags, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user, question, answer, topic, stage, notes, tags_json, now),
    )
    return backend.lastrowid  # type: ignore[return-value]


def delete_bookmark(bookmark_id: int, user: str) -> bool:
    user = (user or "guest").strip() or "guest"
    before = _get_backend().execute(
        "SELECT 1 FROM bookmarks WHERE id=? AND user=?",
        (bookmark_id, user),
    )
    _get_backend().execute(
        "DELETE FROM bookmarks WHERE id=? AND user=?",
        (bookmark_id, user),
    )
    after = _get_backend().execute(
        "SELECT 1 FROM bookmarks WHERE id=? AND user=?",
        (bookmark_id, user),
    )
    return len(before) > 0 and len(after) == 0


def list_bookmarks(user: str, topic: str | None = None, limit: int = 50) -> list[Any]:
    user = (user or "guest").strip() or "guest"
    if topic:
        return _get_backend().execute(
            "SELECT id, user, question, answer, topic, stage, notes, tags, created_at "
            "FROM bookmarks WHERE user=? AND topic=? ORDER BY created_at DESC LIMIT ?",
            (user, topic, limit),
        )
    return _get_backend().execute(
        "SELECT id, user, question, answer, topic, stage, notes, tags, created_at "
        "FROM bookmarks WHERE user=? ORDER BY created_at DESC LIMIT ?",
        (user, limit),
    )


def is_bookmarked(user: str, question: str) -> bool:
    user = (user or "guest").strip() or "guest"
    rows = _get_backend().execute(
        "SELECT 1 FROM bookmarks WHERE user=? AND question=? LIMIT 1",
        (user, question),
    )
    return len(rows) > 0


def update_bookmark_notes(bookmark_id: int, user: str, notes: str) -> bool:
    user = (user or "guest").strip() or "guest"
    _get_backend().execute(
        "UPDATE bookmarks SET notes=? WHERE id=? AND user=?",
        (notes, bookmark_id, user),
    )
    return True


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Full-text search 鈥?interviews
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
def search_interviews(query: str, user: str = "guest", limit: int = 20) -> list[Any]:
    user = (user or "guest").strip() or "guest"
    backend = _get_backend()

    if _FTS_ENABLED and query.strip():
        safe_query = " ".join(
            f'"{term}"*' if " " not in term else f'"{term}"' for term in query.strip().split() if term
        )
        if not safe_query:
            return []
        return backend.execute(
            "SELECT i.id, i.user, i.topic, i.question, i.answer, i.score, i.stage, i.time, i.created_at "
            "FROM interviews_fts, interviews i "
            "WHERE interviews_fts MATCH ? AND interviews_fts.rowid = i.id AND i.user = ? "
            "ORDER BY rank LIMIT ?",
            (safe_query, user, limit),
        )

    pattern = f"%{query}%"
    return backend.execute(
        "SELECT id, user, topic, question, answer, score, stage, time, created_at "
        "FROM interviews WHERE user=? AND (question LIKE ? OR answer LIKE ? OR topic LIKE ?) "
        "ORDER BY time DESC LIMIT ?",
        (user, pattern, pattern, pattern, limit),
    )


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Per-session Reports
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?


def save_report(
    session_id: str,
    user: str,
    topic: str,
    ai_summary: str,
    stats_json: str | None = None,
) -> int:
    """Save or update a per-session AI report. Returns the row id."""
    user = (user or "guest").strip() or "guest"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    backend = _get_backend()

    existing = backend.execute(
        "SELECT id FROM reports WHERE session_id=? AND user=?",
        (session_id, user),
    )
    if existing:
        backend.execute(
            "UPDATE reports SET ai_summary=?, stats_json=?, created_at=? WHERE session_id=? AND user=?",
            (ai_summary, stats_json, now, session_id, user),
        )
        return existing[0]["id"]
    else:
        backend.execute(
            "INSERT INTO reports (session_id, user, topic, ai_summary, stats_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, user, topic, ai_summary, stats_json, now),
        )
        return backend.lastrowid  # type: ignore[return-value]


def load_report(session_id: str, user: str = "guest") -> Any | None:
    """Load a report for a specific session."""
    user = (user or "guest").strip() or "guest"
    rows = _get_backend().execute(
        "SELECT * FROM reports WHERE session_id=? AND user=?",
        (session_id, user),
    )
    return rows[0] if rows else None


def list_report_sessions(user: str = "guest", limit: int = 20) -> list[Any]:
    """List all sessions that have reports, newest first."""
    user = (user or "guest").strip() or "guest"
    return _get_backend().execute(
        "SELECT id, session_id, user, topic, created_at FROM reports WHERE user=? ORDER BY created_at DESC LIMIT ?",
        (user, limit),
    )


def load_user_session_data(session_id: str, user: str = "guest") -> list[Any]:
    """Load interview records for a specific session."""
    user = (user or "guest").strip() or "guest"
    return _get_backend().execute(
        "SELECT id, user, topic, question, answer, score, stage, time, created_at, status, session_id "
        "FROM interviews WHERE session_id=? AND user=? ORDER BY time ASC, id ASC",
        (session_id, user),
    )
