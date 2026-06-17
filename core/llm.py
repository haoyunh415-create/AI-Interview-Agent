"""LLM client factory — supports multiple providers.

Usage::

    from core.llm import get_llm

    llm = get_llm(api_key="sk-...", temperature=0.7)
    llm.invoke("Hello")
    llm.stream("Tell me a story")

Provider is chosen via the ``LLM_PROVIDER`` env var (default: ``deepseek``).

Supported providers: ``deepseek``, ``openai``, ``anthropic``, ``ollama``.

OpenAI-compatible APIs (DeepSeek, OpenAI, and any custom endpoint) all use
``langchain_openai.ChatOpenAI`` under the hood; Anthropic uses
``langchain_anthropic.ChatAnthropic``; Ollama uses ``langchain_ollama.ChatOllama``.
"""

import os
from typing import Any

from core.config import (
    ANTHROPIC_MODEL,
    LLM_BASE_URL,
    LLM_MAX_RETRIES,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TEMPERATURE,
    LLM_TIMEOUT,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)
from core.logging_config import get_logger

_log = get_logger("llm")

# Cache: (api_key_or_empty, provider, temperature) → LLM instance
_llms: dict[tuple[str, str, float], Any] = {}


def get_llm(
    api_key: str | None = None,
    temperature: float | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> Any:
    """Return a cached LLM instance for the active provider.

    Parameters
    ----------
    api_key : str, optional
        API key.  If omitted, resolved from the environment based on provider.
    temperature : float, optional
        Sampling temperature.  Falls back to ``LLM_TEMPERATURE`` from config.
    provider : str, optional
        Provider name (deepseek/openai/anthropic/ollama). Falls back to
        ``LLM_PROVIDER`` env var.
    model : str, optional
        Model name override. Falls back to the provider's default model.

    Returns
    -------
    ChatOpenAI | ChatAnthropic | ChatOllama
        A LangChain chat model instance (duck-typed — all have ``.invoke()``
        and ``.stream()``).
    """
    resolved_provider = provider or (os.getenv("LLM_PROVIDER") or LLM_PROVIDER).lower()

    if api_key is None:
        api_key = _resolve_api_key(resolved_provider)
    if temperature is None:
        temperature = LLM_TEMPERATURE

    key = (api_key or "", resolved_provider, temperature, model or "")
    if key in _llms:
        return _llms[key]

    _log.info(
        "creating new LLM instance: provider=%s model=%s temp=%.1f",
        resolved_provider,
        model or "(default)",
        temperature,
    )
    llm = _create_llm(resolved_provider, api_key, temperature, model)
    _llms[key] = llm
    return llm


def clear_cache() -> None:
    """Clear the LLM instance cache.  Useful after provider switch."""
    _llms.clear()
    _log.info("LLM cache cleared")


def get_provider_info() -> dict[str, str]:
    """Return a dict describing the currently active provider."""
    from core.config import PROVIDER_LABELS, PROVIDER_MODEL_LABELS

    provider = (os.getenv("LLM_PROVIDER") or LLM_PROVIDER).lower()
    return {
        "provider": provider,
        "label": PROVIDER_LABELS.get(provider, provider),
        "model": PROVIDER_MODEL_LABELS.get(provider, "unknown"),
    }


# ══════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════

_API_KEY_ENV_VARS: dict[str, str] = {
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def _resolve_api_key(provider: str) -> str:
    env_var = _API_KEY_ENV_VARS.get(provider)
    if env_var:
        return os.getenv(env_var, "")
    return ""  # Ollama needs no key


def _create_llm(provider: str, api_key: str | None, temperature: float, model: str | None = None) -> Any:
    """Factory: dispatch to the correct provider constructor."""
    from langchain_openai import ChatOpenAI

    if provider == "deepseek":
        return ChatOpenAI(
            model=model or LLM_MODEL,
            api_key=api_key,
            base_url=LLM_BASE_URL,
            temperature=temperature,
            request_timeout=LLM_TIMEOUT,
            max_retries=LLM_MAX_RETRIES,
        )

    if provider == "openai":
        return ChatOpenAI(
            model=model or OPENAI_MODEL,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=OPENAI_BASE_URL,
            temperature=temperature,
            request_timeout=LLM_TIMEOUT,
            max_retries=LLM_MAX_RETRIES,
        )

    if provider == "anthropic":
        return _create_anthropic(api_key, temperature, model)

    if provider == "ollama":
        return _create_ollama(temperature, model)

    raise ValueError(f"Unknown LLM_PROVIDER={provider!r}. Supported: {', '.join(_API_KEY_ENV_VARS.keys())}, ollama")


def _create_anthropic(api_key: str | None, temperature: float, model: str | None = None) -> Any:
    """Create an Anthropic Claude instance."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError("Anthropic provider requires langchain-anthropic. Install: pip install langchain-anthropic")
    return ChatAnthropic(
        model=model or ANTHROPIC_MODEL,
        api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
        temperature=temperature,
        timeout=LLM_TIMEOUT,
        max_retries=LLM_MAX_RETRIES,
    )


def _create_ollama(temperature: float, model: str | None = None) -> Any:
    """Create an Ollama local model instance."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        raise ImportError("Ollama provider requires langchain-ollama. Install: pip install langchain-ollama")
    return ChatOllama(
        model=model or OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        num_predict=2048,
    )
