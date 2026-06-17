"""API key resolution — prefer request-provided key, fall back to server env.

This enables the "server-side proxy" pattern:

1. Set ``DEEPSEEK_API_KEY`` (or another provider's key) in ``.env`` on the server
2. The frontend never needs to send an ``api_key`` field
3. All backend routes fall back to the env var when no key is provided
"""

import os

from core.logging_config import get_logger

_log = get_logger("api_key")

# Providers that have an env var configured
_SERVER_HAS_KEY: bool | None = None


def resolve_api_key(api_key: str | None = None) -> str:
    """Return *api_key* if provided, otherwise resolve from server environment.

    The resolution order:
    1. Explicit ``api_key`` argument
    2. ``DEEPSEEK_API_KEY`` env var
    3. ``OPENAI_API_KEY`` env var
    4. ``ANTHROPIC_API_KEY`` env var
    5. Empty string (Ollama doesn't need one)
    """
    if api_key and api_key.strip():
        return api_key.strip()

    # Try providers in priority order
    for env_var in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        key = os.getenv(env_var, "")
        if key:
            _log.debug("resolved API key from env var %s", env_var)
            return key

    # Ollama — no key needed
    provider = os.getenv("LLM_PROVIDER", "deepseek").lower()
    if provider == "ollama":
        return ""

    _log.warning(
        "No API key provided and no env var found for provider '%s'. LLM calls will fail unless Ollama is used.",
        provider,
    )
    return ""


def server_has_key() -> bool:
    """Check if any API key is configured in the server environment."""
    global _SERVER_HAS_KEY
    if _SERVER_HAS_KEY is not None:
        return _SERVER_HAS_KEY

    for env_var in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        if os.getenv(env_var, ""):
            _SERVER_HAS_KEY = True
            return True

    _SERVER_HAS_KEY = False
    return False


def get_server_provider_info() -> dict:
    """Return provider info for frontend display."""
    from core.config import LLM_PROVIDER, PROVIDER_LABELS, PROVIDER_MODEL_LABELS

    return {
        "server_has_key": server_has_key(),
        "provider": LLM_PROVIDER,
        "label": PROVIDER_LABELS.get(LLM_PROVIDER, LLM_PROVIDER),
        "model": PROVIDER_MODEL_LABELS.get(LLM_PROVIDER, ""),
    }
