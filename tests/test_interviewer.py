"""Tests for Interviewer agent — question generation, followups, hints."""

from agents.interviewer import Interviewer, get_level_bias


class TestGetLevelBias:
    def test_none_profile_returns_empty(self):
        assert get_level_bias(None) == ""

    def test_empty_profile_returns_empty(self):
        assert get_level_bias({}) == ""

    def test_junior_bias(self):
        bias = get_level_bias({"level": "初级"})
        assert "基础概念" in bias
        assert "多给提示" in bias

    def test_mid_bias(self):
        bias = get_level_bias({"level": "中级"})
        assert "进阶" in bias

    def test_senior_bias(self):
        bias = get_level_bias({"level": "高级"})
        assert "架构" in bias

    def test_expert_bias(self):
        bias = get_level_bias({"level": "专家"})
        assert "前沿" in bias

    def test_unknown_level_falls_back_to_mid(self):
        bias = get_level_bias({"level": "unknown"})
        assert "进阶" in bias


class TestInterviewer:
    def test_init_sets_name_and_role(self):
        agent = Interviewer(api_key="test")
        assert agent.name == "interviewer"
        assert "资深的技术面试官" in agent.role

    def test_level_bias_integration(self):
        """Profile with level produces correct bias string."""
        bias = get_level_bias({"level": "高级", "tech_stack": ["Python"]})
        assert bias != ""

    def test_resolve_profile_uses_provided(self):
        agent = Interviewer(api_key="test")
        profile = {"level": "初级", "tech_stack": ["Java"]}
        result = agent._resolve_profile(profile)
        assert result is profile

    def test_resolve_profile_falls_back_to_memory(self):
        from core.memory import SharedMemory
        agent = Interviewer(api_key="test", shared_memory=SharedMemory())
        agent.memory_set("resume.profile", {"level": "高级", "tech_stack": ["Python"]})
        result = agent._resolve_profile(None)
        assert result is not None
        assert result["level"] == "高级"

    def test_resolve_context_uses_provided(self):
        agent = Interviewer(api_key="test")
        result = agent._resolve_context("transformer", context="provided context")
        assert result == "provided context"

    def test_resolve_context_falls_back_to_memory(self):
        from core.memory import SharedMemory
        agent = Interviewer(api_key="test", shared_memory=SharedMemory())
        agent.memory_set("context.Transformer核心原理", "memory context")
        result = agent._resolve_context("Transformer核心原理")
        assert result == "memory context"

    def test_resolve_context_missing_returns_empty(self):
        agent = Interviewer(api_key="test")
        result = agent._resolve_context("nonexistent")
        assert result == ""

    def test_generate_question_with_custom_questions(self):
        agent = Interviewer(api_key="test")
        questions = ["Q1", "Q2", "Q3"]
        result = agent.generate_question(
            topic="Transformer核心原理",
            stage="基础",
            history=[{"q": "previous"}],
            custom_questions=questions,
        )
        # Should return first unused custom question
        assert result == questions[1]  # idx = len(history) = 1

    def test_generate_question_out_of_custom_range(self):
        """When custom_questions are exhausted, fall back to LLM generation."""
        import core.llm_client as llm_client_mod
        from core.mock_llm import MockChatOpenAI

        mock = MockChatOpenAI(
            use_defaults=False,  # prevent accidental key collisions
            default_response="What is self-attention?",
        )
        orig = llm_client_mod.get_llm
        llm_client_mod.get_llm = lambda *a, **kw: mock

        agent = Interviewer(api_key="test")
        try:
            result = agent.generate_question(
                topic="Transformer核心原理",
                stage="基础",
                history=[{"q": "Q1"}, {"q": "Q2"}, {"q": "Q3"}, {"q": "Q4"}, {"q": "Q5"}],
                custom_questions=["Q1", "Q2", "Q3", "Q4", "Q5"],
            )
            assert result == "What is self-attention?"
        finally:
            llm_client_mod.get_llm = orig

    def test_generate_hint_returns_short_prompt(self):
        import core.llm_client as llm_client_mod
        from core.mock_llm import MockChatOpenAI

        mock = MockChatOpenAI(
            use_defaults=False,
            default_response="Think about QKV",
        )
        orig = llm_client_mod.get_llm
        llm_client_mod.get_llm = lambda *a, **kw: mock

        agent = Interviewer(api_key="test")
        try:
            hint = agent.generate_hint("What is attention?")
            assert hint == "Think about QKV"
        finally:
            llm_client_mod.get_llm = orig

    def test_question_prompt_includes_profile(self):
        import core.llm_client as llm_client_mod
        from core.mock_llm import MockChatOpenAI

        mock = MockChatOpenAI()
        orig = llm_client_mod.get_llm
        llm_client_mod.get_llm = lambda *a, **kw: mock

        agent = Interviewer(api_key="test", shared_memory=None)
        try:
            prompt = agent._build_question_prompt(
                topic="RAG",
                stage="基础",
                context="RAG context",
                history=[{"q": "What is RAG?"}],
                profile={"level": "中级", "tech_stack": ["Python", "LangChain"],
                         "domains": ["NLP"]},
            )
            assert "RAG" in prompt
            assert "基础" in prompt
            assert "Python" in prompt
            assert "LangChain" in prompt
            assert "已问过" in prompt
        finally:
            llm_client_mod.get_llm = orig

    def test_followup_prompt_includes_evaluation(self):
        agent = Interviewer(api_key="test")
        prompt = agent._build_followup_prompt(
            original_question="What is RAG?",
            answer="RAG is retrieval augmented generation",
            evaluation={"followup_reason": "lacks detail", "summary": "too brief"},
            stage="基础",
        )
        assert "what is rag?" in prompt.lower()
        assert "lacks detail" in prompt
        assert "too brief" in prompt
        assert "基础" in prompt

    def test_publish_question_event(self):
        from core.memory import MessageBus, SharedMemory
        agent = Interviewer(
            api_key="test",
            shared_memory=SharedMemory(),
            message_bus=MessageBus(),
        )
        agent._publish_question("What is AI?", "基础", is_followup=False)
        latest = agent.message_bus.get_latest("question.generated")
        assert latest is not None
        assert "What is AI?" in str(latest.data)

    def test_publish_followup_event(self):
        from core.memory import MessageBus, SharedMemory
        agent = Interviewer(
            api_key="test",
            shared_memory=SharedMemory(),
            message_bus=MessageBus(),
        )
        agent._publish_question("Any followup?", "进阶", is_followup=True)
        latest = agent.message_bus.get_latest("followup.generated")
        assert latest is not None
        assert "Any followup?" in str(latest.data)
