"""FastAPI backend entry point."""

import contextlib
import os
import sys
import time
import tomllib
import traceback
from unittest.mock import MagicMock

# ════════════════════════════════════════
# ════════════════════════════════════════
# ════════════════════════════════════════
# We don't use any of these packages in this project.
for _mod in ("torch", "transformers", "transformers.utils"):
    sys.modules.setdefault(_mod, MagicMock())

# ════════════════════════════════════════
# No need to call load_dotenv() here.

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.middleware.gzip import GZipMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from slowapi import _rate_limit_exceeded_handler  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402

from backend.api import auth, bookmarks, chat, interview, report, reports, resume, sessions  # noqa: E402
from backend.db.database import init_db  # noqa: E402
from backend.limiter import limiter  # noqa: E402
from core.config import JWT_ALGORITHM, LLM_PROVIDER, SENTRY_DSN, validate_config  # noqa: E402
from core.logging_config import get_logger  # noqa: E402

if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        enable_tracing=True,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )
    get_logger("sentry").info("Sentry error tracking enabled (DSN configured)")

_log = get_logger("api")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan 鈥?initialize on startup, clean up on shutdown."""
    init_db()
    _log.info("Database initialized")

    _log.info("LLM provider: %s", LLM_PROVIDER)
    _log.info("JWT algorithm: %s", JWT_ALGORITHM)
    warnings = validate_config()
    for w in warnings:
        _log.warning("Config: %s", w)
    if not warnings:
        _log.info("All configuration checks passed")

    from agents.knowledge_retriever import create_demo_knowledge_base

    kb_count = create_demo_knowledge_base()
    if kb_count:
        _log.info("Created %d demo knowledge document(s)", kb_count)

    # ===
    # from previous shutdown
    from backend.session_store import restore_sessions

    restored = restore_sessions()
    if restored:
        _log.info("Restored %d session(s) from snapshot on disk", restored)

    from backend.session_store import start_cleanup_task

    start_cleanup_task()

    yield
    _log.info("Shutting down 鈥?persisting sessions...")
    from backend.session_store import persist_all_sessions, stop_cleanup_task

    stop_cleanup_task()
    persist_all_sessions()


# Read version from pyproject.toml at startup
with open("pyproject.toml", "rb") as _f:
    _APP_VERSION = tomllib.load(_f)["project"]["version"]

app = FastAPI(title="AI 闈㈣瘯鍔╂墜", version=_APP_VERSION, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ════════════════════════════════════════
# === CORS ===
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8765",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# ════════════════════════════════════════
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for key, value in SECURITY_HEADERS.items():
        response.headers[key] = value
    return response


# ════════════════════════════════════════
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request with method, path, status, and duration."""
    t0 = time.monotonic()
    try:
        response = await call_next(request)
        elapsed = (time.monotonic() - t0) * 1000
        _log.info(
            "%s %s 鈫?%s (%.0fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response
    except Exception as exc:
        elapsed = (time.monotonic() - t0) * 1000
        _log.error(
            "%s %s 鈫?ERROR %s (%.0fms)",
            request.method,
            request.url.path,
            exc,
            elapsed,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": type(exc).__name__, "status_code": 500},
        )


# ════════════════════════════════════════
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Standardized HTTP error response: ``{"detail": ..., "type": ..., "status_code": ...}``."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "type": "HTTPException",
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic validation errors 鈫?readable 400 response."""
    errors = [
        {"loc": " 鈫?".join(str(part) for part in err["loc"]), "msg": err["msg"], "type": err["type"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "type": "ValidationError",
            "errors": errors,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    _log.warning("ValueError: %s", exc)
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "ValueError", "status_code": 400},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    _log.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__, "status_code": 500},
    )


# ════════════════════════════════════════
# ════════════════════════════════════════
# Legacy unversioned routes (backward compatible)
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(resume.router, prefix="/api", tags=["resume"])
app.include_router(interview.router, prefix="/api", tags=["interview"])
app.include_router(report.router, prefix="/api", tags=["report"])
app.include_router(bookmarks.router, prefix="/api", tags=["bookmarks"])
app.include_router(sessions.router, prefix="/api", tags=["sessions"])

# Versioned routes (preferred for new code)
app.include_router(auth.router, prefix="/api/v1", tags=["api"])
app.include_router(chat.router, prefix="/api/v1", tags=["api"])
app.include_router(resume.router, prefix="/api/v1", tags=["api"])
app.include_router(interview.router, prefix="/api/v1", tags=["api"])
app.include_router(report.router, prefix="/api/v1", tags=["api"])
app.include_router(bookmarks.router, prefix="/api/v1", tags=["api"])
app.include_router(sessions.router, prefix="/api/v1", tags=["api"])

# Reports (read-only history)
app.include_router(reports.router, prefix="/api", tags=["api"])
app.include_router(reports.router, prefix="/api/v1", tags=["api"])


# ════════════════════════════════════════
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?


@app.get("/api/config")
def app_config() -> dict:
    """Return server configuration for the frontend.

    The frontend uses this to determine whether to show/hide the
    API key field, which LLM provider is configured, etc.
    """
    from core.api_key import get_server_provider_info

    return get_server_provider_info()


# Health
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
_APP_START_TIME = time.monotonic()


@app.get("/api/health")
def health() -> dict:
    from backend.session_store import get_session_count

    # DB check
    db_ok = False
    try:
        from backend.db.database import _get_backend

        _get_backend().execute("SELECT 1")
        db_ok = True
    except Exception:
        pass

    # LLM cache info
    from agents.base import BaseAgent

    cache_stats = BaseAgent.cache_info()

    # Uptime
    uptime_seconds = int(time.monotonic() - _APP_START_TIME)

    return {
        "status": "ok",
        "version": _APP_VERSION,
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{uptime_seconds // 3600}h{(uptime_seconds % 3600) // 60}m{uptime_seconds % 60}s",
        "llm_provider": LLM_PROVIDER,
        "db_connected": db_ok,
        "cache": cache_stats,
        "active_sessions": get_session_count(),
    }
