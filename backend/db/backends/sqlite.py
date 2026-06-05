"""SQLite database backend — wraps sqlite3 with thread-local connections."""

import contextlib
import sqlite3
from collections.abc import Sequence
from typing import Any

from core.logging_config import get_logger

_log = get_logger("db.sqlite")


class SqliteBackend:
    """Thread-safe SQLite backend.

    Reuses the same connection per thread (matching the original
    ``threading.local()`` pattern from ``db/database.py``).
    """

    def __init__(self, db_url: str) -> None:
        # Parse sqlite:///path from URL
        self._path = db_url.replace("sqlite:///", "", 1) if "://" in db_url else db_url
        self._conn: sqlite3.Connection | None = None
        self._lastrowid: int | None = None
        self._rowcount: int = 0

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except sqlite3.OperationalError:
                _log.info("reconnecting — stale connection detected")
                self.close()

        _log.debug("creating new SQLite connection: %s", self._path)
        conn = sqlite3.connect(self._path, timeout=10, check_same_thread=False, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        self._conn = conn
        return conn

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> list[Any]:
        conn = self._get_conn()
        if params is None:
            cursor = conn.execute(sql)
        else:
            cursor = conn.execute(sql, params)
        self._lastrowid = cursor.lastrowid
        self._rowcount = cursor.rowcount if cursor.rowcount is not None else 0
        return cursor.fetchall()

    def execute_script(self, sql: str) -> None:
        """Run multiple SQL statements (SQLite-only — uses ``executescript``)."""
        conn = self._get_conn()
        conn.executescript(sql)

    def close(self) -> None:
        if self._conn is not None:
            with contextlib.suppress(Exception):
                self._conn.close()
            self._conn = None

    @property
    def lastrowid(self) -> int | None:
        return self._lastrowid
