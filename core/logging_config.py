"""Centralized logging configuration — dev-friendly or JSON for production.

Usage::

    from core.logging_config import get_logger

    log = get_logger("my.module")
    log.info("hello %s", name)
    log_duration(log, "operation", start_time)
"""

import json
import logging
import os
import sys
import time

from core.config import LOG_LEVEL

_loggers: dict[str, dict] = {}

_LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

# When LOG_FORMAT=json, outputs structured JSON lines (production-friendly)
_LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()


class JsonFormatter(logging.Formatter):
    """JSON log formatter for production (log aggregation systems)."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }, ensure_ascii=False)


def setup_logging(level: int | None = None) -> logging.Logger:
    if level is None:
        level = _LEVEL_MAP.get(LOG_LEVEL.upper(), logging.INFO)
    root = logging.getLogger("tech-chat")
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)

    if _LOG_FORMAT == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)-5s] %(name)s - %(message)s",
                datefmt="%m-%d %H:%M:%S",
            )
        )

    root.addHandler(handler)
    root.propagate = False
    logging.getLogger("uvicorn.access").handlers.clear()
    return root


def get_logger(name: str | None = None) -> logging.Logger:
    if name:
        full = f"tech-chat.{name}"
    else:
        full = "tech-chat"

    if full not in _loggers:
        _loggers[full] = logging.getLogger(full)

    return _loggers[full]


def log_duration(logger: logging.Logger, label: str, start_time: float) -> None:
    elapsed = (time.monotonic() - start_time) * 1000
    logger.info("%s completed in %.0fms", label, elapsed)


setup_logging()
