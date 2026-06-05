"""Base agent class with LLM invocation, streaming, and JSON parsing.

Slim public-facing layer that composes three specialised collaborators:

* ``LlmClient`` — raw LLM calls (invoke / stream / ainvoke)
* ``LlmCache`` — LRU response cache shared across all agents
* ``TelemetryCollector`` — per-call tracing and metrics

Every agent also optionally has ``SharedMemory`` + ``MessageBus`` for
inter-agent communication.
"""

import json
import re
import time
from collections.abc import Iterator
from typing import Any

from core.cache import llm_cache
from core.llm_client import LlmClient, resolve_api_key
from core.logging_config import get_logger, log_duration


class BaseAgent:
    """Base class for all agents. Provides invoke, stream, and JSON parsing.

    LLM response caching is enabled globally via ``LLM_CACHE_TTL`` and
    ``LLM_CACHE_MAXSIZE`` in config.  Use ``skip_cache=True`` on any call
    to bypass (e.g. evaluation, where freshness matters).
    """

    # ── Class-level cache helpers (delegate to module-level singleton) ──

    @classmethod
    def clear_response_cache(cls) -> None:
        """Clear the global LLM response cache."""
        llm_cache.clear()

    @classmethod
    def cache_info(cls) -> dict[str, int]:
        """Return cache stats for monitoring."""
        return llm_cache.info()

    # ═════════════════════════════════════════════════════
    # Construction
    # ═════════════════════════════════════════════════════

    def __init__(
        self,
        name: str,
        role: str,
        temperature: float | None = None,
        api_key: str | None = None,
        shared_memory: Any = None,   # SharedMemory (or None)
        message_bus: Any = None,     # MessageBus  (or None)
        telemetry: Any = None,       # TelemetryCollector (or None)
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self._temperature = temperature
        self._logger = get_logger(f"agent.{name}")

        # Resolve API key: explicit > provider-specific env var
        resolved_provider = provider or "deepseek"
        resolved_key = api_key or resolve_api_key(resolved_provider)

        # ── Delegated collaborators ──
        self._llm = LlmClient(
            api_key=resolved_key,
            provider=resolved_provider,
            model=model,
            temperature=temperature,
        )
        self.telemetry = telemetry

        # ── Inter-agent communication ──
        self.shared_memory = shared_memory
        self.message_bus = message_bus

    # ═════════════════════════════════════════════════════
    # Public API: invoke — composes cache → LLM → telemetry
    # ═════════════════════════════════════════════════════

    def invoke(self, prompt: str, temperature: float | None = None, skip_cache: bool = False) -> str:
        """Invoke LLM with optional response caching.

        When *skip_cache* is ``True`` (e.g. evaluation), bypasses the cache
        so the LLM always generates a fresh response.
        """
        full_prompt = f"{self.role}\n\n{prompt}"
        temp = temperature if temperature is not None else self._temperature

        # 1. Check cache
        if not skip_cache:
            cached = llm_cache.get(full_prompt, temp or 0)
            if cached is not None:
                return cached

        self._logger.info("cache MISS (temp=%.1f, prompt_len=%d)", temp or 0, len(full_prompt))

        # 2. Raw LLM call
        t0 = time.monotonic()
        try:
            result, usage = self._llm.invoke(full_prompt, temperature)
            elapsed = (time.monotonic() - t0) * 1000

            # 3. Telemetry
            self._record_telemetry("invoke", full_prompt, result, elapsed, success=True,
                                   temperature=temp or 0, **usage)

            # 4. Store in cache
            if not skip_cache:
                llm_cache.set(full_prompt, temp or 0, result)

            log_duration(self._logger, f"invoke [{self.name}]", t0)
            return result

        except Exception as exc:
            elapsed = (time.monotonic() - t0) * 1000
            self._record_telemetry("invoke", full_prompt, "", elapsed,
                                   success=False, error=str(exc), temperature=temp or 0)
            raise

    # ═════════════════════════════════════════════════════
    # Public API: invoke_stream — composes cache → stream → telemetry
    # ═════════════════════════════════════════════════════

    def invoke_stream(
        self, prompt: str, temperature: float | None = None, skip_cache: bool = False
    ) -> Iterator[str]:
        """Yield tokens one at a time. Caches full response after completion."""
        full_prompt = f"{self.role}\n\n{prompt}"
        temp = temperature if temperature is not None else self._temperature

        # 1. Check cache
        if not skip_cache:
            cached = llm_cache.get(full_prompt, temp or 0)
            if cached is not None:
                yield cached
                return

        self._logger.info("stream cache MISS (temp=%.1f, prompt_len=%d)", temp or 0, len(full_prompt))

        # 2. Raw streaming via LlmClient
        t0 = time.monotonic()
        response_parts: list[str] = []

        try:
            for chunk in self._llm.stream(full_prompt, temperature):
                response_parts.append(chunk)
                yield chunk

            elapsed = (time.monotonic() - t0) * 1000
            full_response = "".join(response_parts)

            # 3. Store in cache
            if not skip_cache and full_response:
                llm_cache.set(full_prompt, temp or 0, full_response)

            # 4. Telemetry
            self._record_telemetry("invoke_stream", full_prompt, full_response, elapsed,
                                   success=True, temperature=temp or 0)

        except Exception as exc:
            elapsed = (time.monotonic() - t0) * 1000
            response_text = "".join(response_parts)
            self._record_telemetry("invoke_stream", full_prompt, response_text, elapsed,
                                   success=False, error=str(exc), temperature=temp or 0)
            raise
        finally:
            log_duration(self._logger, f"invoke_stream [{self.name}]", t0)

    # ═════════════════════════════════════════════════════
    # Public API: ainvoke — async version (avoids blocking event loop)
    # ═════════════════════════════════════════════════════

    async def ainvoke(self, prompt: str, temperature: float | None = None, skip_cache: bool = False) -> str:
        """Async LLM invoke with optional response caching.

        Same as :meth:`invoke` but ``await``-able so the event loop isn't
        blocked during the LLM call.  Use this in async FastAPI routes.
        """
        full_prompt = f"{self.role}\n\n{prompt}"
        temp = temperature if temperature is not None else self._temperature

        # 1. Check cache
        if not skip_cache:
            cached = llm_cache.get(full_prompt, temp or 0)
            if cached is not None:
                return cached

        self._logger.info("async cache MISS (temp=%.1f, prompt_len=%d)", temp or 0, len(full_prompt))

        # 2. Raw LLM call (async via LlmClient)
        t0 = time.monotonic()
        try:
            result, usage = await self._llm.ainvoke(full_prompt, temperature)
            elapsed = (time.monotonic() - t0) * 1000

            # 3. Telemetry
            self._record_telemetry("ainvoke", full_prompt, result, elapsed, success=True,
                                   temperature=temp or 0, **usage)

            # 4. Store in cache
            if not skip_cache:
                llm_cache.set(full_prompt, temp or 0, result)

            log_duration(self._logger, f"ainvoke [{self.name}]", t0)
            return result

        except Exception as exc:
            elapsed = (time.monotonic() - t0) * 1000
            self._record_telemetry("ainvoke", full_prompt, "", elapsed,
                                   success=False, error=str(exc), temperature=temp or 0)
            raise

    # ═════════════════════════════════════════════════════
    # JSON helpers
    # ═════════════════════════════════════════════════════

    def invoke_json(
        self, prompt: str, temperature: float | None = None, skip_cache: bool = False
    ) -> dict[str, Any]:
        """Invoke LLM and parse JSON from response."""
        raw = self.invoke(prompt, temperature, skip_cache=skip_cache)
        return self._parse_json(raw)

    async def ainvoke_json(
        self, prompt: str, temperature: float | None = None, skip_cache: bool = False
    ) -> dict[str, Any]:
        """Async LLM invoke and parse JSON from response."""
        raw = await self.ainvoke(prompt, temperature, skip_cache=skip_cache)
        return self._parse_json(raw)

    def invoke_json_safe(
        self,
        prompt: str,
        fallback: dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """Like invoke_json, but returns a fallback dict on parse failure."""
        try:
            return self.invoke_json(prompt, temperature)
        except ValueError:
            return fallback or {"raw": "", "error": "JSON parse failed"}

    # ═════════════════════════════════════════════════════
    # JSON parsing helpers
    # ═════════════════════════════════════════════════════

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        """Parse JSON from raw LLM output without calling the LLM again."""
        for pattern in [
            r"\{(?:[^{}]|\{[^{}]*\})*\}",
            r"\{.*?\}",
        ]:
            match = re.search(pattern, raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    continue

        start = raw.find("{")
        if start != -1:
            depth = 0
            for i in range(start, len(raw)):
                if raw[i] == "{":
                    depth += 1
                elif raw[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(raw[start : i + 1])
                        except json.JSONDecodeError:
                            break

        raise ValueError(
            f"Failed to parse JSON from LLM output. "
            f"Raw response (first 200 chars): {raw[:200]}"
        )

    # ═════════════════════════════════════════════════════
    # Inter-agent communication helpers
    # ═════════════════════════════════════════════════════

    def publish_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event to the message bus (no-op if not configured)."""
        if self.message_bus is not None:
            self.message_bus.publish(event_type, data, self.name)
            self._logger.debug("published event=%s", event_type)

    def memory_get(self, key: str, default: Any = None) -> Any:
        """Read a value from shared memory."""
        if self.shared_memory is not None:
            return self.shared_memory.get(key, default)
        return default

    def memory_set(self, key: str, value: Any, metadata: dict | None = None) -> None:
        """Write a value to shared memory."""
        if self.shared_memory is not None:
            self.shared_memory.set(key, value, self.name, metadata)

    def memory_latest(self, ns: str) -> tuple[str, Any] | None:
        """Get the most recent (key, value) in namespace *ns*."""
        if self.shared_memory is not None:
            return self.shared_memory.get_latest_in_namespace(ns)
        return None

    # ═════════════════════════════════════════════════════
    # Telemetry helper
    # ═════════════════════════════════════════════════════

    def _record_telemetry(
        self,
        method: str,
        prompt: str,
        response_text: str,
        latency_ms: float,
        success: bool = True,
        error: str = "",
        temperature: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Record an LLM call trace in the telemetry collector (if configured)."""
        if self.telemetry is not None:
            self.telemetry.trace(
                agent=self.name,
                method=method,
                prompt_len=len(prompt),
                response_len=len(response_text),
                latency_ms=latency_ms,
                success=success,
                error=error,
                temperature=temperature,
                input_tokens=input_tokens or None,
                output_tokens=output_tokens or None,
            )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
