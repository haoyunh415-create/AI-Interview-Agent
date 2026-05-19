import json
import os
import sqlite3
from datetime import datetime

from core.config import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "interview.db")


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _column_names(conn, table):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with _connect() as conn:
        conn.execute("""
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

        columns = _column_names(conn, "interviews")
        if "created_at" not in columns:
            conn.execute("ALTER TABLE interviews ADD COLUMN created_at TEXT")
            conn.execute("UPDATE interviews SET created_at = COALESCE(time, datetime('now', 'localtime'))")

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_interviews_user_time
            ON interviews(user, time, id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_interviews_topic
            ON interviews(topic)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_interviews_stage
            ON interviews(stage)
        """)


def _serialize_score(score):
    if isinstance(score, (dict, list)):
        return json.dumps(score, ensure_ascii=False)
    return "" if score is None else str(score)


def save(user, topic, q, a, score, stage):
    user = (user or "guest").strip() or "guest"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO interviews
                (user, topic, question, answer, score, stage, time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user, topic, q, a, _serialize_score(score), stage, now, now),
        )


def load_user(user, limit=None):
    user = (user or "guest").strip() or "guest"
    query = """
        SELECT id, user, topic, question, answer, score, stage, time, created_at
        FROM interviews
        WHERE user = ?
        ORDER BY time ASC, id ASC
    """
    params = [user]
    if limit:
        query += " LIMIT ?"
        params.append(int(limit))

    with _connect() as conn:
        return conn.execute(query, params).fetchall()


def load_user_stats(user):
    user = (user or "guest").strip() or "guest"
    with _connect() as conn:
        return conn.execute(
            """
            SELECT
                COUNT(*) AS total_questions,
                COUNT(DISTINCT topic) AS topics_covered,
                COUNT(DISTINCT stage) AS stages_covered,
                MAX(time) AS last_time
            FROM interviews
            WHERE user = ?
            """,
            (user,),
        ).fetchone()
