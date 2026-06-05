"""Database backend 鈥?supports SQLite (default) and PostgreSQL.

Usage::

    from backend.db.backend import get_backend

    backend = get_backend()
    rows = backend.execute("SELECT * FROM interviews WHERE user = ?", ("guest",))
    backend.lastrowid  # if you need it

Backend selection via ``DB_URL`` environment variable:
  - ``sqlite:///./data/interview.db`` 鈫?SQLite (default)
  - ``postgresql://user:pass@host:5432/dbname`` 鈫?PostgreSQL (psycopg2)

All backends:
  - Accept ``?`` placeholders (converted to ``%s`` for PostgreSQL)
  - Return rows that support ``row["column"]`` access
  - Use thread-local connections (one connection per thread)
"""

import os
import threading
from collections.abc import Sequence
from typing import Any

from core.config import DATA_DIR

# 鈹€鈹€ Default to SQLite 鈹€鈹€
_DEFAULT_DB_URL = f"sqlite:///{DATA_DIR}/interview.db"
DB_URL: str = os.getenv("DB_URL", _DEFAULT_DB_URL)

_log = None  # lazy import


def _log_info(msg: str, *args: Any) -> None:
    global _log
    if _log is None:
        from core.logging_config import get_logger
        _log = get_logger("db.backend")
    _log.info(msg, *args)


def _log_warn(msg: str, *args: Any) -> None:
    global _log
    if _log is None:
        from core.logging_config import get_logger
        _log = get_logger("db.backend")
    _log.warning(msg, *args)


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Backend selection
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
_local = threading.local()


def get_backend() -> Any:
    """Get the database backend for the current thread.

    Creates one per thread (thread-local singleton).  The returned object
    has ``execute(sql, params) -> list[dict]`` and ``.lastrowid``.
    """
    backend: Any = getattr(_local, "backend", None)
    if backend is not None:
        try:
            backend.execute("SELECT 1")
            return backend
        except Exception:
            _local.backend = None

    uri = DB_URL
    if uri.startswith("postgresql"):
        _log_info("creating PostgreSQL backend: %s", uri)
        from backend.db.backends.postgres import PostgresBackend
        backend = PostgresBackend(uri)
    else:
        _log_info("creating SQLite backend: %s", uri)
        from backend.db.backends.sqlite import SqliteBackend
        backend = SqliteBackend(uri)

    _local.backend = backend
    return backend


def reset_backend() -> None:
    """Close and clear the cached backend for this thread."""
    backend: Any = getattr(_local, "backend", None)
    if backend is not None:
        try:
            backend.close()
        except Exception:
            pass
        _local.backend = None
