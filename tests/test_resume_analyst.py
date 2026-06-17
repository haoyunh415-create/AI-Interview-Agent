"""Tests for ResumeAnalyst agent — profile extraction and sharing."""

import json

from agents.resume_analyst import ResumeAnalyst


class TestResumeAnalyst:
    def test_init_sets_name_and_role(self):
        agent = ResumeAnalyst(api_key="test")
        assert agent.name == "resume_analyst"
        assert "简历分析师" in agent.role

    def test_analyze_with_empty_resume_returns_fallback(self):
        from core.memory import SharedMemory

        agent = ResumeAnalyst(
            api_key="test",
            shared_memory=SharedMemory(),
        )
        result = agent.analyze("")
        assert result["tech_stack"] == []
        assert result["level"] == "未知"
        assert result["years_of_experience"] == 0

    def test_analyze_with_whitespace_returns_fallback(self):
        agent = ResumeAnalyst(api_key="test")
        result = agent.analyze("   \n  \n  ")
        assert result["tech_stack"] == []

    def test_analyze_writes_to_shared_memory(self):
        import core.llm_client as llm_client_mod
        from core.memory import SharedMemory
        from core.mock_llm import MockChatOpenAI

        mock = MockChatOpenAI(
            responses={
                "简历分析": json.dumps(
                    {
                        "tech_stack": ["Python", "PyTorch"],
                        "level": "中级",
                        "domains": ["NLP"],
                        "gaps": ["MLOps"],
                        "highlights": ["Built a RAG system"],
                        "years_of_experience": 3,
                    }
                ),
            }
        )
        orig = llm_client_mod.get_llm
        llm_client_mod.get_llm = lambda *a, **kw: mock

        memory = SharedMemory()
        agent = ResumeAnalyst(api_key="test", shared_memory=memory)
        try:
            profile = agent.analyze("5 years Python experience at tech company")
            assert profile["tech_stack"] == ["Python", "PyTorch"]
            assert profile["level"] == "中级"

            # Verify shared memory
            mem_profile = memory.get("resume.profile")
            assert mem_profile is not None
            assert mem_profile["level"] == "中级"
        finally:
            llm_client_mod.get_llm = orig

    def test_analyze_publishes_event(self):
        import core.llm_client as llm_client_mod
        from core.memory import MessageBus, SharedMemory
        from core.mock_llm import MockChatOpenAI

        mock = MockChatOpenAI(
            responses={
                "简历分析": json.dumps(
                    {
                        "tech_stack": ["Python"],
                        "level": "初级",
                        "domains": [],
                        "gaps": [],
                        "highlights": [],
                        "years_of_experience": 1,
                    }
                ),
            }
        )
        orig = llm_client_mod.get_llm
        llm_client_mod.get_llm = lambda *a, **kw: mock

        bus = MessageBus()
        agent = ResumeAnalyst(
            api_key="test",
            shared_memory=SharedMemory(),
            message_bus=bus,
        )
        try:
            agent.analyze("Junior Python dev")
            event = bus.get_latest("resume.analyzed")
            assert event is not None
            assert "profile" in event.data
        finally:
            llm_client_mod.get_llm = orig

    def test_analyze_stores_level_and_tech_stack_separately(self):
        import core.llm_client as llm_client_mod
        from core.memory import SharedMemory
        from core.mock_llm import MockChatOpenAI

        mock = MockChatOpenAI(
            responses={
                "简历分析": json.dumps(
                    {
                        "tech_stack": ["Go", "Kubernetes"],
                        "level": "高级",
                        "domains": ["Infra"],
                        "gaps": ["AI"],
                        "highlights": ["Designed microservices"],
                        "years_of_experience": 5,
                    }
                ),
            }
        )
        orig = llm_client_mod.get_llm
        llm_client_mod.get_llm = lambda *a, **kw: mock

        memory = SharedMemory()
        agent = ResumeAnalyst(api_key="test", shared_memory=memory)
        try:
            agent.analyze("Senior backend engineer with Go experience")
            assert memory.get("resume.level") == "高级"
            assert memory.get("resume.tech_stack") == ["Go", "Kubernetes"]
        finally:
            llm_client_mod.get_llm = orig

    def test_analyze_fallback_on_llm_failure(self):
        """When LLM returns bad JSON, invoke_json_safe returns fallback."""
        import core.llm_client as llm_client_mod
        from core.memory import SharedMemory
        from core.mock_llm import MockChatOpenAI

        mock = MockChatOpenAI(
            use_defaults=False,  # prevent "简历分析" key collision
            default_response="Not JSON at all, just plain text",
        )
        orig = llm_client_mod.get_llm
        llm_client_mod.get_llm = lambda *a, **kw: mock

        agent = ResumeAnalyst(api_key="test", shared_memory=SharedMemory())
        try:
            result = agent.analyze("Some resume text here")
            # Should return fallback with empty arrays
            assert isinstance(result, dict)
            assert result["tech_stack"] == []
            assert result["level"] == "未知"
        finally:
            llm_client_mod.get_llm = orig

    def test_resolve_profile_structure(self):
        """Verify the structure keys exist in analyzed profile."""
        import core.llm_client as llm_client_mod
        from core.mock_llm import MockChatOpenAI

        mock = MockChatOpenAI(
            responses={
                "简历分析": json.dumps(
                    {
                        "tech_stack": ["Python"],
                        "level": "中级",
                        "domains": ["NLP", "CV"],
                        "gaps": ["MLOps"],
                        "highlights": ["RAG system"],
                        "years_of_experience": 2,
                    }
                ),
            }
        )
        orig = llm_client_mod.get_llm
        llm_client_mod.get_llm = lambda *a, **kw: mock

        agent = ResumeAnalyst(api_key="test")
        try:
            result = agent.analyze("Data scientist 2 years")
            assert set(result.keys()) >= {
                "tech_stack",
                "level",
                "domains",
                "gaps",
                "highlights",
                "years_of_experience",
            }
            assert isinstance(result["tech_stack"], list)
            assert isinstance(result["domains"], list)
            assert isinstance(result["years_of_experience"], int)
        finally:
            llm_client_mod.get_llm = orig
