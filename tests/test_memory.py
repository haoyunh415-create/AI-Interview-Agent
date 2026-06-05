"""Tests for SharedMemory and MessageBus — inter-agent communication core."""


from core.memory import Events, Message, MessageBus, SharedMemory

# ═══════════════════════════════════════════════════════
# SharedMemory
# ═══════════════════════════════════════════════════════

class TestSharedMemory:
    def test_set_and_get(self):
        mem = SharedMemory()
        mem.set("resume.level", "高级", "resume_analyst")
        assert mem.get("resume.level") == "高级"

    def test_get_default(self):
        mem = SharedMemory()
        assert mem.get("nonexistent", "fallback") == "fallback"
        assert mem.get("nonexistent") is None

    def test_get_entry_returns_provenance(self):
        mem = SharedMemory()
        mem.set("context.rag", "RAG content", "knowledge_retriever")
        entry = mem.get_entry("context.rag")
        assert entry is not None
        assert entry.source == "knowledge_retriever"
        assert entry.value == "RAG content"
        assert entry.seq > 0  # monotonic sequence number
        assert entry.timestamp > 0

    def test_get_namespace(self):
        mem = SharedMemory()
        mem.set("resume.level", "中级", "resume_analyst")
        mem.set("resume.tech_stack", ["Python"], "resume_analyst")
        mem.set("context.transformer", "content", "knowledge_retriever")
        ns = mem.get_namespace("resume")
        assert ns["resume.level"] == "中级"
        assert ns["resume.tech_stack"] == ["Python"]
        assert "context.transformer" not in ns

    def test_get_latest_in_namespace_returns_last_written(self):
        mem = SharedMemory()
        mem.set("eval.round1", {"score": 5}, "evaluator")
        mem.set("eval.round2", {"score": 8}, "evaluator")
        key, val = mem.get_latest_in_namespace("eval")
        assert key == "eval.round2", f"expected round2, got {key}"
        assert val["score"] == 8

    def test_get_latest_in_namespace_respects_seq_even_with_rapid_writes(self):
        """Sequence number guarantees determinism regardless of clock resolution."""
        mem = SharedMemory()
        for i in range(100):
            mem.set(f"eval.r{i}", {"i": i}, "evaluator")
        key, _val = mem.get_latest_in_namespace("eval")
        assert key == "eval.r99"

    def test_get_latest_in_empty_ns(self):
        mem = SharedMemory()
        assert mem.get_latest_in_namespace("empty") is None

    def test_clear(self):
        mem = SharedMemory()
        mem.set("a.b", 1, "agent")
        assert len(mem.keys()) == 1
        mem.clear()
        assert len(mem.keys()) == 0

    def test_remove(self):
        mem = SharedMemory()
        mem.set("a.b", 1, "agent")
        mem.remove("a.b")
        assert mem.get("a.b") is None
        assert "a" not in mem._ns_index or "a.b" not in mem._ns_index["a"]

    def test_to_dict(self):
        mem = SharedMemory()
        mem.set("resume.level", "初级", "resume_analyst", {"model": "deepseek"})
        d = mem.to_dict()
        assert "resume.level" in d
        assert d["resume.level"]["value"] == "初级"
        assert d["resume.level"]["source"] == "resume_analyst"
        assert d["resume.level"]["metadata"]["model"] == "deepseek"

    def test_keys_with_ns(self):
        mem = SharedMemory()
        mem.set("a.x", 1, "a1")
        mem.set("a.y", 2, "a1")
        mem.set("b.z", 3, "b1")
        assert set(mem.keys("a")) == {"a.x", "a.y"}
        assert mem.keys("b") == ["b.z"]

    def test_overwrite_same_key(self):
        mem = SharedMemory()
        mem.set("resume.level", "初级", "agent_a")
        mem.set("resume.level", "高级", "agent_b")
        assert mem.get("resume.level") == "高级"
        entry = mem.get_entry("resume.level")
        assert entry.source == "agent_b"
        assert entry.seq > 0


# ═══════════════════════════════════════════════════════
# MessageBus
# ═══════════════════════════════════════════════════════

class TestMessageBus:
    def test_publish_returns_message(self):
        bus = MessageBus()
        msg = bus.publish("test.event", {"key": "val"}, "tester")
        assert isinstance(msg, Message)
        assert msg.type == "test.event"
        assert msg.data["key"] == "val"
        assert msg.source == "tester"
        assert len(msg.id) == 8

    def test_get_history(self):
        bus = MessageBus()
        bus.publish("a", {"n": 1}, "src")
        bus.publish("a", {"n": 2}, "src")
        bus.publish("b", {"n": 3}, "src")
        hist = bus.get_history("a")
        assert len(hist) == 2
        assert hist[0].data["n"] == 1
        assert hist[1].data["n"] == 2

    def test_get_history_all(self):
        bus = MessageBus()
        bus.publish("a", {}, "s")
        bus.publish("b", {}, "s")
        assert len(bus.get_history()) == 2

    def test_get_latest(self):
        bus = MessageBus()
        assert bus.get_latest("nonexistent") is None
        bus.publish("x", {"v": 1}, "s")
        bus.publish("x", {"v": 2}, "s")
        latest = bus.get_latest("x")
        assert latest is not None and latest.data["v"] == 2

    def test_subscribe_receives_published(self):
        bus = MessageBus()
        received: list[Message] = []
        bus.subscribe("my.event", lambda m: received.append(m))
        bus.publish("my.event", {"msg": "hello"}, "tester")
        assert len(received) == 1
        assert received[0].data["msg"] == "hello"

    def test_subscribe_only_own_type(self):
        bus = MessageBus()
        received: list[Message] = []
        bus.subscribe("type_a", lambda m: received.append(m))
        bus.publish("type_b", {}, "s")
        assert len(received) == 0

    def test_subscribe_all(self):
        bus = MessageBus()
        received: list[str] = []
        bus.subscribe_all(lambda m: received.append(m.type))
        bus.publish("a", {}, "s")
        bus.publish("b", {}, "s")
        assert received == ["a", "b"]

    def test_unsubscribe(self):
        bus = MessageBus()
        def cb(m: Message): pass
        bus.subscribe("ev", cb)
        bus.unsubscribe("ev", cb)

        # Subscriber list should be empty now
        received: list[Message] = []
        bus.subscribe("ev", lambda m: received.append(m))
        assert len(received) == 0

    def test_max_history_eviction(self):
        bus = MessageBus(max_history=3)
        for i in range(5):
            bus.publish("ev", {"i": i}, "s")
        assert len(bus.get_history()) == 3
        assert bus.get_history()[-1].data["i"] == 4

    def test_subscriber_error_does_not_crash(self):
        bus = MessageBus()
        def failing(_m):
            raise RuntimeError("oops")
        bus.subscribe("ev", failing)
        # This should not raise
        bus.publish("ev", {}, "s")
        bus.publish("ev", {}, "s")

    def test_history_limit(self):
        bus = MessageBus()
        for i in range(20):
            bus.publish("ev", {"i": i}, "s")
        hist = bus.get_history("ev", limit=5)
        assert len(hist) == 5
        assert hist[-1].data["i"] == 19


# ═══════════════════════════════════════════════════════
# Events constants
# ═══════════════════════════════════════════════════════

class TestEvents:
    def test_constants_are_strings(self):
        assert isinstance(Events.RESUME_ANALYZED, str)
        assert isinstance(Events.ANSWER_EVALUATED, str)

    def test_all_lifecycle_events_defined(self):
        expected = {
            "resume.analyzed",
            "context.retrieved",
            "question.generated",
            "answer.evaluated",
            "followup.generated",
            "stage.completed",
            "report.generated",
        }
        assert set(Events.LIFECYCLE) == expected


# ═══════════════════════════════════════════════════════
# Integration: SharedMemory + MessageBus together
# ═══════════════════════════════════════════════════════

class TestMemoryBusIntegration:
    def test_agent_writes_memory_and_notifies_bus(self):
        """Simulate the ResumeAnalyst flow."""
        mem = SharedMemory()
        bus = MessageBus()

        # Agent writes to memory and publishes
        profile = {"level": "高级", "tech_stack": ["Python", "PyTorch"]}
        mem.set("resume.profile", profile, "resume_analyst")
        bus.publish(Events.RESUME_ANALYZED, {"profile": profile}, "resume_analyst")

        # Another agent reads from memory
        assert mem.get("resume.profile")["level"] == "高级"

        # Or subscribes to events
        received: list[Message] = []
        bus.subscribe(Events.RESUME_ANALYZED, lambda m: received.append(m))
        bus.publish(Events.RESUME_ANALYZED, {"profile": profile}, "resume_analyst")
        assert len(received) == 1

    def test_full_lifecycle_events(self):
        """Simulate a complete interview lifecycle through the bus."""
        mem = SharedMemory()
        bus = MessageBus()
        timeline: list[str] = []
        bus.subscribe_all(lambda m: timeline.append(m.type))

        # Stage 1: Resume analyzed
        profile = {"level": "初级"}
        mem.set("resume.profile", profile, "resume_analyst")
        bus.publish(Events.RESUME_ANALYZED, {}, "resume_analyst")

        # Stage 2: Context retrieved
        mem.set("context.Transformer", "attention is all you need", "knowledge_retriever")
        bus.publish(Events.CONTEXT_RETRIEVED, {}, "knowledge_retriever")

        # Stage 3: Question generated
        bus.publish(Events.QUESTION_GENERATED, {}, "interviewer")

        # Stage 4: Answer evaluated
        mem.set("eval.latest", {"correctness": 7}, "evaluator")
        bus.publish(Events.ANSWER_EVALUATED, {}, "evaluator")

        # Stage 5: Report generated
        bus.publish(Events.REPORT_GENERATED, {}, "report_writer")

        assert timeline == [
            Events.RESUME_ANALYZED,
            Events.CONTEXT_RETRIEVED,
            Events.QUESTION_GENERATED,
            Events.ANSWER_EVALUATED,
            Events.REPORT_GENERATED,
        ]
        assert mem.get("resume.profile")["level"] == "初级"
