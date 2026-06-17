"""PostgreSQL database backend — uses psycopg2.

Converts ``?`` placeholders to ``%s`` internally so the rest of the
codebase can use the same query syntax as SQLite.
"""

import contextlib
import re
from collections.abc import Sequence
from typing import Any

from core.logging_config import get_logger

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover — psycopg2 is optional
    psycopg2 = None  # type: ignore[assignment]

_log = get_logger("db.postgres")


def _convert_placeholders(sql: str) -> str:
    """Convert SQLite ``?`` placeholders to PostgreSQL ``%s``."""
    result, _ = re.subn(r"(?<!\?)%(?!\s|$)", r"%%", sql)  # escape existing %s
    result, _ = re.subn(r"\?", r"%s", result)
    return result


class PostgresBackend:
    """Thread-safe PostgreSQL backend.

    Uses ``psycopg2`` with ``RealDictCursor`` for row-dict compatibility.
    """

    def __init__(self, db_url: str) -> None:
        self._db_url = db_url
        self._conn: Any = None
        self._lastrowid: int | None = None

    def _get_conn(self) -> Any:
        if self._conn is not None:
            try:
                cur = self._conn.cursor()
                cur.execute("SELECT 1")
                cur.close()
                return self._conn
            except Exception:
                _log.info("reconnecting — stale PostgreSQL connection")
                self.close()

        _log.info("creating new PostgreSQL connection: %s", self._db_url)
        self._conn = psycopg2.connect(self._db_url)
        self._conn.autocommit = True
        return self._conn

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> list[Any]:
        conn = self._get_conn()
        pg_sql = _convert_placeholders(sql)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            if params is None:
                cur.execute(pg_sql)
            else:
                cur.execute(pg_sql, params)
            rows = cur.fetchall()
            self._lastrowid = cur.lastrowid if hasattr(cur, "lastrowid") else None
            return [dict(row) for row in rows] if rows else []
        finally:
            cur.close()

    def executemany(self, sql: str, params_list: Sequence[Sequence[Any]]) -> None:
        conn = self._get_conn()
        pg_sql = _convert_placeholders(sql)
        cur = conn.cursor()
        try:
            from psycopg2.extras import execute_values

            execute_values(cur, pg_sql, params_list)
        finally:
            cur.close()

    def close(self) -> None:
        if self._conn is not None:
            with contextlib.suppress(Exception):
                self._conn.close()
            self._conn = None

    @property
    def lastrowid(self) -> int | None:
        return self._lastrowid
