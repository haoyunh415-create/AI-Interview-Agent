"""Initial schema matching ``db/database.py:init_db()``.

Revision ID: e391ca02688d
Revises: None
Create Date: 2026-06-03

This migration is the source of truth for the database schema.
After applying it, the app's ``init_db()`` will find all tables
exist and skip the CREATE TABLE / ALTER TABLE logic.

Generated hand-aligned from the raw SQL in ``db/database.py``.
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text as sa_text


revision: str = "e391ca02688d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── interviews ──
    op.execute(sa_text("""
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
    """))
    op.execute(sa_text("""
        CREATE INDEX IF NOT EXISTS idx_interviews_user_time
        ON interviews(user, time, id)
    """))
    op.execute(sa_text("""
        CREATE INDEX IF NOT EXISTS idx_interviews_topic
        ON interviews(topic)
    """))
    op.execute(sa_text("""
        CREATE INDEX IF NOT EXISTS idx_interviews_stage
        ON interviews(stage)
    """))
    op.execute(sa_text("""
        CREATE INDEX IF NOT EXISTS idx_interviews_question
        ON interviews(question)
    """))

    # ── sessions ──
    op.execute(sa_text("""
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
    """))
    op.execute(sa_text("""
        CREATE INDEX IF NOT EXISTS idx_sessions_user_status
        ON sessions(user, status)
    """))
    op.execute(sa_text("""
        CREATE INDEX IF NOT EXISTS idx_sessions_updated
        ON sessions(updated_at)
    """))

    # ── users (auth) ──
    op.execute(sa_text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """))
    op.execute(sa_text("""
        CREATE INDEX IF NOT EXISTS idx_users_username
        ON users(username)
    """))

    # ── bookmarks ──
    op.execute(sa_text("""
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
    """))
    op.execute(sa_text("""
        CREATE INDEX IF NOT EXISTS idx_bookmarks_user
        ON bookmarks(user, created_at)
    """))

    # ── FTS5 virtual table (optional — silently skipped if fts5 not available) ──
    try:
        op.execute(sa_text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS interviews_fts
            USING fts5(user, topic, question, answer,
                       content='interviews', content_rowid='id')
        """))
    except Exception:
        # FTS5 not available — the app handles this gracefully
        pass


def downgrade() -> None:
    """Drop all tables created by the upgrade."""
    op.execute(sa_text("DROP TABLE IF EXISTS bookmarks"))
    op.execute(sa_text("DROP TABLE IF EXISTS users"))
    op.execute(sa_text("DROP TABLE IF EXISTS sessions"))
    op.execute(sa_text("DROP TABLE IF EXISTS interviews"))
    op.execute(sa_text("DROP TABLE IF EXISTS interviews_fts"))

