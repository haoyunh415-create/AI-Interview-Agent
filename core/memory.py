"""Shared Memory and Message Bus for inter-agent communication.

Agents use SharedMemory to share structured data (resume profiles, knowledge
context, evaluation scores) and MessageBus to notify each other when important
events occur. This eliminates the orchestrator having to manually pass data
as string concatenation between agents.

Event dispatch is **asynchronous** — subscribers are scheduled as background
tasks so a slow subscriber never blocks the publisher or other subscribers.
"""

import asyncio
import contextlib
import random
import string
import time
from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from core.logging_config import get_logger

_log = get_logger("memory")


# ═══════════════════════════════════════════════════════
# Shared Memory
# ═══════════════════════════════════════════════════════

_write_counter: int = 0  # module-level monotonic sequence for deterministic ordering


@dataclass
class MemoryEntry:
    """A single entry in shared memory with provenance tracking.

    Every write records which agent wrote it and when, enabling downstream
    agents to judge staleness or source credibility.
    """

    value: Any
    source: str
    timestamp: float = field(default_factory=time.monotonic)
    seq: int = field(default_factory=lambda: _increment_seq())
    metadata: dict = field(default_factory=dict)


def _increment_seq() -> int:
    global _write_counter
    _write_counter += 1
    return _write_counter


class SharedMemory:
    """Namespaced key-value store for inter-agent state sharing.

    Agents write their outputs here so other agents can discover them without
    the orchestrator manually passing data.  Namespace convention::

        resume.{field}     — resume analysis results
        context.{field}    — knowledge retrieval results (per topic)
        interview.{field}  — interview state (stage, history, scores)
        eval.{field}       — latest evaluation results
        agent.{name}.{key} — free-form notes from a specific agent

    All writes are append-only within a session; there is no compaction.
    A ``clear()`` is performed by the orchestrator on reset.
    """

    def __init__(self) -> None:
        self._store: dict[str, MemoryEntry] = {}
        self._ns_index: dict[str, set[str]] = defaultdict(set)

    # ── Write API ──

    def set(
        self,
        key: str,
        value: Any,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ns = key.split(".", 1)[0] if "." in key else "_root"
        self._store[key] = MemoryEntry(
            value=value,
            source=source,
            metadata=metadata or {},
        )
        self._ns_index[ns].add(key)
        _log.debug("mem W source=%s  ns=%s  key=%s  type=%s", source, ns, key, type(value).__name__)

    # ── Read API ──

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._store.get(key)
        return entry.value if entry is not None else default

    def get_entry(self, key: str) -> MemoryEntry | None:
        return self._store.get(key)

    def get_namespace(self, ns: str) -> dict[str, Any]:
        """Return all key → value pairs under *ns* as a flat dict."""
        return {key: self._store[key].value for key in self._ns_index.get(ns, set()) if key in self._store}

    def get_latest_in_namespace(self, ns: str) -> tuple[str, Any] | None:
        """Return (key, value) of the most recently written entry in *ns*.

        Deterministic ordering: later writes always win, even when
        wall-clock timestamps are identical.  Returns ``None`` if the
        namespace is empty.
        """
        best_key: str | None = None
        best_seq = -1
        for key in self._ns_index.get(ns, set()):
            entry = self._store.get(key)
            if entry is not None and entry.seq > best_seq:
                best_key, best_seq = key, entry.seq
        if best_key is None:
            return None
        return best_key, self._store[best_key].value

    # ── Introspection ──

    def __iter__(self) -> Iterator[str]:
        """Iterate over all keys in the store."""
        return iter(self._store)

    def keys(self, ns: str | None = None) -> list[str]:
        if ns is not None:
            return list(self._ns_index.get(ns, set()))
        return list(self._store.keys())

    def clear(self) -> None:
        self._store.clear()
        self._ns_index.clear()

    def remove(self, key: str) -> None:
        if key in self._store:
            ns = key.split(".", 1)[0] if "." in key else "_root"
            self._ns_index[ns].discard(key)
            del self._store[key]

    def to_dict(self) -> dict[str, Any]:
        """Serialize memory to a JSON-safe dict.

        The returned dict has shape ``{key: {value, source, metadata}}``
        and can be restored via ``load_dict()``.
        """
        return {key: {"value": e.value, "source": e.source, "metadata": e.metadata} for key, e in self._store.items()}

    def load_dict(self, data: dict[str, Any]) -> None:
        """Restore memory from a dict previously returned by ``to_dict()``.

        This is **additive** — existing keys with the same name are
        overwritten; keys not in *data* are left untouched.  Use
        ``clear()`` first if you want a clean slate.
        """
        if not data:
            return
        for key, entry in data.items():
            if not isinstance(entry, dict):
                continue
            self.set(
                key=key,
                value=entry.get("value"),
                source=entry.get("source", "restore"),
                metadata=entry.get("metadata"),
            )


# ═══════════════════════════════════════════════════════
# Message Bus
# ═══════════════════════════════════════════════════════


@dataclass
class Message:
    """A structured event published by an agent via the message bus."""

    type: str
    data: dict[str, Any]
    source: str
    timestamp: float = field(default_factory=time.time)
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


class MessageBus:
    """Publish-subscribe event bus for agent communication.

    Usage::

        bus = MessageBus()
        bus.publish("resume.analyzed", {"profile": {...}}, "resume_analyst")
        bus.subscribe("answer.evaluated", my_callback)
    """

    def __init__(self, max_history: int = 200) -> None:
        self._subscribers: dict[str, list[Callable[[Message], Any]]] = defaultdict(list)
        self._wildcard_subscribers: list[Callable[[Message], Any]] = []
        self._history: list[Message] = []
        self._max_history = max_history

    # ── Dispatch helpers ──

    @staticmethod
    def _dispatch_callbacks(callbacks: list[Callable], msg: Message, label: str) -> None:
        """Dispatch *callbacks* concurrently.

        If an asyncio event loop is running in the current thread, callbacks
        are scheduled as background tasks so a slow subscriber never blocks
        the publisher.  Otherwise (sync tests, non-async contexts) fall back
        to sequential execution.
        """
        try:
            loop = asyncio.get_running_loop()
            in_async = True
        except RuntimeError:
            in_async = False

        if in_async:
            for cb in callbacks:

                async def _invoke(cb: Callable = cb) -> None:
                    try:
                        if asyncio.iscoroutinefunction(cb):
                            await cb(msg)
                        else:
                            cb(msg)
                    except Exception as exc:
                        _log.error("bus async %s FAILED: %s", label, exc)

                _task = loop.create_task(_invoke())  # noqa: RUF006
        else:
            for cb in callbacks:
                try:
                    cb(msg)
                except Exception as exc:
                    _log.error("bus %s FAILED: %s", label, exc)

    # ── Publish ──

    def publish(self, type: str, data: dict[str, Any], source: str) -> Message:
        msg = Message(type=type, data=data, source=source)
        self._history.append(msg)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        _log.info("bus >>> type=%s  source=%s  data_keys=%s", type, source, list(data.keys()))

        # Notify type-specific subscribers
        type_cbs = self._subscribers.get(type, [])
        self._dispatch_callbacks(type_cbs, msg, f"type={type}")

        # Notify wildcard subscribers
        self._dispatch_callbacks(self._wildcard_subscribers, msg, "wildcard")

        return msg

    # ── Subscribe ──

    def subscribe(self, type: str, callback: Callable[[Message], Any]) -> None:
        self._subscribers[type].append(callback)

    def subscribe_all(self, callback: Callable[[Message], Any]) -> None:
        """Subscribe to *every* event type."""
        self._wildcard_subscribers.append(callback)

    def unsubscribe(self, type: str, callback: Callable[[Message], Any]) -> None:
        with contextlib.suppress(ValueError):
            self._subscribers[type].remove(callback)

    # ── History ──

    def get_history(self, type: str | None = None, limit: int = 50) -> list[Message]:
        if type is None:
            return self._history[-limit:]
        relevant = [m for m in self._history if m.type == type]
        return relevant[-limit:]

    def get_latest(self, type: str) -> Message | None:
        """Return the most recent message of *type*, or ``None``."""
        for msg in reversed(self._history):
            if msg.type == type:
                return msg
        return None


# ═══════════════════════════════════════════════════════
# Canonical event types
# ═══════════════════════════════════════════════════════


class Events:
    """Well-known event type constants used across all agents."""

    RESUME_ANALYZED = "resume.analyzed"
    CONTEXT_RETRIEVED = "context.retrieved"
    QUESTION_GENERATED = "question.generated"
    FOLLOWUP_GENERATED = "followup.generated"
    ANSWER_EVALUATED = "answer.evaluated"
    STAGE_COMPLETED = "stage.completed"
    REPORT_GENERATED = "report.generated"
    HINT_REQUESTED = "hint.requested"
    CUSTOM_QUESTIONS_READY = "custom_job.questions_ready"

    # Interview lifecycle shortcuts for orchestrator subscriptions
    LIFECYCLE = (
        RESUME_ANALYZED,
        CONTEXT_RETRIEVED,
        QUESTION_GENERATED,
        ANSWER_EVALUATED,
        FOLLOWUP_GENERATED,
        STAGE_COMPLETED,
        REPORT_GENERATED,
    )
