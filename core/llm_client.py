"""Low-level LLM client — raw invoke / stream / ainvoke with token extraction.

This is the **single responsibility** layer for talking to LLM providers.
It does NOT handle caching, telemetry, or agent-level concerns — those are
composed by ``BaseAgent`` using this client, ``LlmCache``, and
``TelemetryCollector``.

Usage::

    from core.llm_client import LlmClient

    client = LlmClient(api_key="...", provider="deepseek", temperature=0.7)
    text, usage = client.invoke("Hello")
    for token in client.stream("Tell me a story"):
        ...
"""

import asyncio
import os
from collections.abc import Iterator
from typing import Any

# Re-export the provider info function so callers don't need to know about core.llm
from core.llm import clear_cache as clear_llm_instances  # noqa: F401
from core.llm import (
    get_llm,
    get_provider_info,  # noqa: F401
)

# ── Provider API key env-var map ──

_API_KEY_ENV_VARS: dict[str, str] = {
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def resolve_api_key(provider: str) -> str:
    """Resolve the API key from the environment for the given provider."""
    env_var = _API_KEY_ENV_VARS.get(provider)
    if env_var:
        return os.getenv(env_var, "")
    return ""  # Ollama needs no key


# ══════════════════════════════════════════════════════════
# Token usage extraction
# ══════════════════════════════════════════════════════════


def extract_usage(response: Any) -> dict[str, int]:
    """Extract real token counts from API response metadata."""
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        um = response.usage_metadata
        return {
            "input_tokens": um.get("input_tokens", 0),
            "output_tokens": um.get("output_tokens", 0),
        }
    if hasattr(response, "response_metadata"):
        meta = response.response_metadata or {}
        token_usage = meta.get("token_usage", {})
        if token_usage:
            return {
                "input_tokens": token_usage.get("prompt_tokens", 0),
                "output_tokens": token_usage.get("completion_tokens", 0),
            }
    return {}


def extract_usage_from_chunk(last_chunk: Any) -> dict[str, int]:
    """Extract token counts from the last streaming chunk."""
    if last_chunk is not None and hasattr(last_chunk, "usage_metadata") and last_chunk.usage_metadata:
        return {
            "input_tokens": last_chunk.usage_metadata.get("input_tokens", 0),
            "output_tokens": last_chunk.usage_metadata.get("output_tokens", 0),
        }
    return {}


# ══════════════════════════════════════════════════════════
# LlmClient
# ══════════════════════════════════════════════════════════


class LlmClient:
    """Thin wrapper over the LangChain LLM instance.

    Holds a reference to a configured (provider, model, api_key, temperature)
    instance and exposes ``invoke``, ``stream``, and ``ainvoke`` that return
    ``(text, usage_dict)`` tuples.
    """

    def __init__(
        self,
        api_key: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        self._api_key = api_key
        self._provider = provider
        self._model = model
        self._temperature = temperature

    # ── Synchronous invoke ──

    def invoke(self, prompt: str, temperature: float | None = None) -> tuple[str, dict[str, int]]:
        """Raw LLM invoke. Returns ``(response_text, usage_dict)``."""
        llm = self._get_llm(temperature)
        response = llm.invoke(prompt)
        return response.content, extract_usage(response)

    # ── Streaming ──

    def stream(self, prompt: str, temperature: float | None = None) -> Iterator[str]:
        """Raw LLM stream. Yields text tokens."""
        llm = self._get_llm(temperature)
        for chunk in llm.stream(prompt):
            if chunk.content:
                yield chunk.content

    # ── Async invoke ──

    async def ainvoke(self, prompt: str, temperature: float | None = None) -> tuple[str, dict[str, int]]:
        """Async raw LLM invoke. Runs sync call in thread pool."""
        llm = self._get_llm(temperature)
        response = await asyncio.to_thread(llm.invoke, prompt)
        return response.content, extract_usage(response)

    # ── LLM instance (delegates to core.llm factory) ──

    def _get_llm(self, temperature: float | None = None) -> Any:
        """Get or create a configured LangChain chat model instance."""
        temp = temperature if temperature is not None else self._temperature
        return get_llm(
            api_key=self._api_key,
            temperature=temp,
            provider=self._provider,
            model=self._model,
        )
