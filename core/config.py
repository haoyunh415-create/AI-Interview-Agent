"""Centralized configuration constants.

All values can be overridden via environment variables (prefixed where noted).
Use ``from core.config import settings`` for typed access.

Note: ``.env`` is loaded here so that *any* import of this module picks up
environment variables.  This avoids the pitfall of importing config before
``load_dotenv()`` has been called.
"""

import os
from dataclasses import dataclass

# ── Load .env file at the earliest possible point ──
# (before any os.getenv calls below)
from dotenv import load_dotenv
load_dotenv()

# ── Paths ──
DATA_DIR = os.getenv("DATA_DIR", "./data")

# ── Sentry error tracking ──
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# ── LLM Provider (default: deepseek) ──
# Supported: deepseek, openai, anthropic, ollama
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek").lower()

# DeepSeek (default)
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")

# OpenAI (used when LLM_PROVIDER=openai)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Anthropic (used when LLM_PROVIDER=anthropic)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# Ollama (used when LLM_PROVIDER=ollama — no API key needed)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Shared LLM settings
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))

# ── Logging ──
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ── Interview ──
# 每阶段最大追问次数
MAX_FOLLOWUPS_PER_STAGE = int(os.getenv("MAX_FOLLOWUPS_PER_STAGE", "3"))
# STAGES 定义见 core/constants.py（单一定点）

# ── Interview timer (optional countdown per question) ──
TIMER_ENABLED = os.getenv("TIMER_ENABLED", "false").lower() == "true"
TIMER_DURATION = int(os.getenv("TIMER_DURATION", "120"))

# ── LLM response cache ──
LLM_CACHE_TTL = int(os.getenv("LLM_CACHE_TTL", "300"))        # 5 minutes default
LLM_CACHE_MAXSIZE = int(os.getenv("LLM_CACHE_MAXSIZE", "256"))  # max entries

# ── JWT Auth ──
_JWT_ENV_SECRET = os.getenv("JWT_SECRET", "")


def _resolve_jwt_secret() -> str:
    """Resolve JWT secret with automatic first-run generation.

    Priority:
    1. ``JWT_SECRET`` env var
    2. ``.jwt_secret.key`` file (auto-generated on first start)
    3. Generate a new random secret and persist to file
    """
    if _JWT_ENV_SECRET:
        if _JWT_ENV_SECRET == "change-me-in-production":
            import warnings
            warnings.warn(
                "JWT_SECRET is still set to the default 'change-me-in-production'! "
                "Set a strong random secret via env var, or delete the env var to "
                "auto-generate one.",
                RuntimeWarning, stacklevel=2,
            )
        return _JWT_ENV_SECRET

    secret_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".jwt_secret.key")
    if os.path.exists(secret_file):
        with open(secret_file, encoding="utf-8") as f:
            return f.read().strip()

    # Generate a new random secret
    import secrets
    new_secret = secrets.token_hex(64)
    try:
        with open(secret_file, "w", encoding="utf-8") as f:
            f.write(new_secret)
        os.chmod(secret_file, 0o600)  # only owner can read (Unix)
    except OSError:
        pass  # non-fatal — fall through to in-memory usage
    return new_secret


JWT_SECRET = _resolve_jwt_secret()
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "72"))

# ── Rate limiting ──
RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "30/minute")   # general endpoints
RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "5/minute")          # register/login
RATE_LIMIT_LLM = os.getenv("RATE_LIMIT_LLM", "10/minute")
RETRIEVAL_SCORE_THRESHOLD = 0.5           # LLM endpoints


@dataclass
class Settings:
    """Strongly-typed settings bag — access via ``settings.LLM_MODEL`` etc.

    Useful when you want to pass a config object around instead of importing
    module-level constants.  For backwards compatibility the module-level
    constants above remain in place and reference this bag.
    """
    # Paths
    DATA_DIR: str = DATA_DIR
    # LLM
    LLM_PROVIDER: str = LLM_PROVIDER
    LLM_MODEL: str = LLM_MODEL
    LLM_BASE_URL: str = LLM_BASE_URL
    OPENAI_API_KEY: str = OPENAI_API_KEY
    OPENAI_MODEL: str = OPENAI_MODEL
    OPENAI_BASE_URL: str = OPENAI_BASE_URL
    ANTHROPIC_API_KEY: str = ANTHROPIC_API_KEY
    ANTHROPIC_MODEL: str = ANTHROPIC_MODEL
    OLLAMA_BASE_URL: str = OLLAMA_BASE_URL
    OLLAMA_MODEL: str = OLLAMA_MODEL
    LLM_TEMPERATURE: float = LLM_TEMPERATURE
    LLM_TIMEOUT: int = LLM_TIMEOUT
    LLM_MAX_RETRIES: int = LLM_MAX_RETRIES
    # Logging
    LOG_LEVEL: str = LOG_LEVEL
    # Interview
    MAX_FOLLOWUPS_PER_STAGE: int = MAX_FOLLOWUPS_PER_STAGE
    TIMER_ENABLED: bool = TIMER_ENABLED
    TIMER_DURATION: int = TIMER_DURATION
    # LLM Cache
    LLM_CACHE_TTL: int = LLM_CACHE_TTL
    LLM_CACHE_MAXSIZE: int = LLM_CACHE_MAXSIZE
    # JWT Auth
    JWT_SECRET: str = JWT_SECRET
    JWT_ALGORITHM: str = JWT_ALGORITHM
    JWT_EXPIRY_HOURS: int = JWT_EXPIRY_HOURS
    # Rate limiting
    RATE_LIMIT_DEFAULT: str = RATE_LIMIT_DEFAULT
    RATE_LIMIT_AUTH: str = RATE_LIMIT_AUTH
    RATE_LIMIT_LLM: str = RATE_LIMIT_LLM
    # Sentry
    SENTRY_DSN: str = SENTRY_DSN


settings = Settings()

# ── Provider display names ──

PROVIDER_LABELS: dict[str, str] = {
    "deepseek": "DeepSeek",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "ollama": "Ollama (Local)",
}

PROVIDER_MODEL_LABELS: dict[str, str] = {
    "deepseek": LLM_MODEL,
    "openai": OPENAI_MODEL,
    "anthropic": ANTHROPIC_MODEL,
    "ollama": OLLAMA_MODEL,
}


# ═══════════════════════════════════════════════════════
# Configuration validation
# ═══════════════════════════════════════════════════════

_CONFIG_WARNINGS: list[str] = []


def validate_config() -> list[str]:
    """Validate critical configuration at startup.

    Returns a list of warning messages.  Call this once during app startup
    (e.g. in the FastAPI lifespan) to fail fast with clear diagnostics.
    """
    global _CONFIG_WARNINGS
    _CONFIG_WARNINGS = []
    warnings_list = _CONFIG_WARNINGS

    # ── JWT Secret ──
    if JWT_SECRET == "change-me-in-production":
        warnings_list.append(
            "JWT_SECRET is still set to the DEFAULT value 'change-me-in-production'! "
            "Set a strong random secret via env var, or delete the env var to "
            "auto-generate one."
        )
    elif len(JWT_SECRET) < 32:
        warnings_list.append(
            f"JWT_SECRET is only {len(JWT_SECRET)} characters long. "
            "For production, use at least 32 characters (auto-generated is 128)."
        )

    # ── Active provider's API key ──
    _API_KEY_CHECKS: dict[str, tuple[str, str]] = {
        "deepseek": ("DEEPSEEK_API_KEY", "DeepSeek"),
        "openai": ("OPENAI_API_KEY", "OpenAI"),
        "anthropic": ("ANTHROPIC_API_KEY", "Anthropic"),
    }
    if LLM_PROVIDER in _API_KEY_CHECKS:
        env_var, label = _API_KEY_CHECKS[LLM_PROVIDER]
        if not os.getenv(env_var, ""):
            warnings_list.append(
                f"LLM_PROVIDER is '{LLM_PROVIDER}' but {env_var} is not set. "
                f"The {label} API will fail at runtime unless a key is provided "
                f"per-request from the frontend."
            )

    # ── DATA_DIR ──
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
        except OSError as exc:
            warnings_list.append(
                f"DATADIR '{DATA_DIR}' doesn't exist and can't be created: {exc}. "
                "The database layer will fail at first use."
            )

    # ── Rate limiting ──
    if os.getenv("DISABLE_RATE_LIMIT"):
        warnings_list.append(
            "DISABLE_RATE_LIMIT is set — rate limiting is disabled. "
            "This is fine for development but NOT for production."
        )

    # ── CORS origins ──
    allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8765")
    if "*" in allowed:
        warnings_list.append(
            "ALLOWED_ORIGINS contains '*' — CORS is wide open. "
            "Restrict to specific origins in production."
        )

    for msg in warnings_list:
        import logging
        logging.getLogger("config").warning("Config: %s", msg)

    return warnings_list


def get_config_warnings() -> list[str]:
    """Return warnings accumulated from the last ``validate_config()`` call."""
    return _CONFIG_WARNINGS
