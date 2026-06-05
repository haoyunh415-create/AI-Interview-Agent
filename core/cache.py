"""LLM response cache — LRU with TTL, shared across all agents.

Usage::

    from core.cache import llm_cache

    llm_cache.clear()
    info = llm_cache.info()
    cached = llm_cache.get(prompt, temperature)
    llm_cache.set(prompt, temperature, response_text)
"""

import hashlib

from cachetools import TTLCache

from core.config import LLM_CACHE_MAXSIZE, LLM_CACHE_TTL
from core.logging_config import get_logger

_log = get_logger("cache")


class LlmCache:
    """LRU cache for LLM responses, keyed by SHA-256 of prompt + temperature.

    This is a **shared** cache — all agents use the same pool so that
    identical prompts (e.g. the same resume analysis) hit once regardless
    of which agent initiated the call.
    """

    def __init__(self, maxsize: int = LLM_CACHE_MAXSIZE, ttl: int = LLM_CACHE_TTL) -> None:
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)

    # ── Key generation ──

    @staticmethod
    def _make_key(prompt: str, temperature: float) -> str:
        """Deterministic cache key from prompt + temperature."""
        raw = f"{temperature}|{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()

    # ── Public API ──

    def get(self, prompt: str, temperature: float) -> str | None:
        """Return cached response, or ``None`` on miss."""
        key = self._make_key(prompt, temperature)
        cached = self._cache.get(key)
        if cached is not None:
            _log.info("cache HIT (temp=%.1f, prompt_len=%d)", temperature, len(prompt))
        return cached

    def set(self, prompt: str, temperature: float, value: str) -> None:
        """Store a response in the cache."""
        key = self._make_key(prompt, temperature)
        self._cache[key] = value

    def clear(self) -> None:
        """Evict all entries."""
        self._cache.clear()
        _log.info("LLM response cache cleared")

    def info(self) -> dict[str, int]:
        """Return cache statistics for monitoring."""
        return {
            "size": self._cache.currsize,
            "maxsize": self._cache.maxsize,
            "ttl_seconds": self._cache.ttl,
        }


# Module-level singleton — shared across all agents
llm_cache = LlmCache()
