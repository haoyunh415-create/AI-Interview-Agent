"""Telemetry — LLM call tracing and structured session metrics.

Every LLM call through ``BaseAgent.invoke()`` / ``invoke_stream()`` is
recorded as a ``TraceEntry`` in the ``TelemetryCollector``.  The collector
accumulates per-agent and per-session aggregates that can be rendered in
the sidebar dashboard or exported for analysis.

Token tracking has two tiers:
1. **Real** (preferred): extracted from API ``response_metadata.token_usage``
2. **Estimated** (fallback): ``input_tokens ≈ len(prompt) / 3.5``, ``output_tokens ≈ len(response) / 4``
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from core.logging_config import get_logger

_log = get_logger("telemetry")


# ═══════════════════════════════════════════════════════
# Trace entry
# ═══════════════════════════════════════════════════════

@dataclass
class TraceEntry:
    """Record of a single LLM call.

    If *input_tokens* or *output_tokens* are given (from API metadata), they
    are used as-is.  Otherwise they are estimated from character lengths.
    """
    agent: str
    method: str          # "invoke" | "invoke_stream" | "invoke_json"
    prompt_len: int
    response_len: int
    latency_ms: float
    # Real token counts (from API response metadata, 0 = not available)
    input_tokens: int = 0
    output_tokens: int = 0
    success: bool = True
    error: str = ""
    temperature: float = 0.0

    def __post_init__(self) -> None:
        # Estimate when real token counts are absent (mock LLM, older API)
        if not self.input_tokens:
            self.input_tokens = max(1, int(self.prompt_len / 3.5))
        if not self.output_tokens:
            self.output_tokens = max(1, int(self.response_len / 4))


# ═══════════════════════════════════════════════════════
# Agent-level aggregates
# ═══════════════════════════════════════════════════════

@dataclass
class AgentStats:
    """Aggregated metrics for a single agent."""
    call_count: int = 0
    total_latency_ms: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    error_count: int = 0

    @property
    def avg_latency_ms(self) -> float:
        if self.call_count == 0:
            return 0.0
        return round(self.total_latency_ms / self.call_count, 1)

    @property
    def avg_total_tokens(self) -> int:
        if self.call_count == 0:
            return 0
        return (self.total_input_tokens + self.total_output_tokens) // self.call_count


# ═══════════════════════════════════════════════════════
# TelemetryCollector
# ═══════════════════════════════════════════════════════

class TelemetryCollector:
    """Accumulates LLM call traces and produces session-level metrics.

    Usage::

        telemetry = TelemetryCollector()
        telemetry.trace(TraceEntry(agent="interviewer", method="invoke", ...))
        stats = telemetry.get_agent_stats()   # → {"interviewer": AgentStats(...)}
        summary = telemetry.summary()          # → {total_calls, total_latency, ...}
        telemetry.reset()                      # start fresh
    """

    def __init__(self, max_traces: int = 500) -> None:
        self._traces: list[TraceEntry] = []
        self._max_traces = max_traces
        self._start_time = time.monotonic()

    # ── Record ──

    def record(self, entry: TraceEntry) -> None:
        self._traces.append(entry)
        if len(self._traces) > self._max_traces:
            self._traces.pop(0)
        _log.debug("trace agent=%s method=%s latency=%.0fms", entry.agent, entry.method, entry.latency_ms)

    def trace(
        self,
        agent: str,
        method: str,
        prompt_len: int,
        response_len: int,
        latency_ms: float,
        success: bool = True,
        error: str = "",
        temperature: float = 0.0,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> TraceEntry:
        """Convenience: create and record a TraceEntry in one call."""
        entry = TraceEntry(
            agent=agent,
            method=method,
            prompt_len=prompt_len,
            response_len=response_len,
            latency_ms=latency_ms,
            input_tokens=input_tokens or 0,
            output_tokens=output_tokens or 0,
            success=success,
            error=error,
            temperature=temperature,
        )
        self.record(entry)
        return entry

    # ── Query ──

    def get_agent_stats(self) -> dict[str, AgentStats]:
        """Aggregate per-agent metrics from all traces."""
        agg: dict[str, AgentStats] = defaultdict(AgentStats)
        for t in self._traces:
            s = agg[t.agent]
            s.call_count += 1
            s.total_latency_ms += t.latency_ms
            s.total_input_tokens += t.input_tokens
            s.total_output_tokens += t.output_tokens
            if not t.success:
                s.error_count += 1
        return dict(agg)

    def get_recent_traces(self, limit: int = 10) -> list[TraceEntry]:
        """Most recent traces, newest first."""
        return list(reversed(self._traces[-limit:]))

    def summary(self) -> dict[str, Any]:
        """Session-level summary dict (useful for UI display)."""
        if not self._traces:
            return {"total_calls": 0, "total_latency_ms": 0, "total_tokens": 0,
                    "agents": {}, "elapsed_seconds": 0}

        agent_stats = self.get_agent_stats()
        total_calls = sum(s.call_count for s in agent_stats.values())
        total_latency = sum(s.total_latency_ms for s in agent_stats.values())
        total_tokens = sum(s.total_input_tokens + s.total_output_tokens for s in agent_stats.values())
        total_errors = sum(s.error_count for s in agent_stats.values())

        return {
            "total_calls": total_calls,
            "total_latency_ms": round(total_latency, 1),
            "total_tokens": total_tokens,
            "total_errors": total_errors,
            "elapsed_seconds": round(time.monotonic() - self._start_time, 1),
            "agents": {
                name: {
                    "calls": s.call_count,
                    "avg_latency_ms": s.avg_latency_ms,
                    "total_tokens": s.total_input_tokens + s.total_output_tokens,
                    "errors": s.error_count,
                }
                for name, s in sorted(agent_stats.items())
            },
        }

    def reset(self) -> None:
        self._traces.clear()
        self._start_time = time.monotonic()

    @property
    def trace_count(self) -> int:
        return len(self._traces)
