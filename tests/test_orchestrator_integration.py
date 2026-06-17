"""Integration tests for the full agent pipeline with mock LLM.

Exercises the complete interview lifecycle through InterviewOrchestrator
without any real API calls.  The mock LLM validates prompt construction
and return-value handling at every stage.
"""

import json
import os
import shutil
import tempfile

import pytest

from agents.orchestrator import InterviewOrchestrator
from backend.db.database import init_db, set_db_path
from core.memory import Events
from core.mock_llm import MockChatOpenAI


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Fixtures
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
@pytest.fixture(autouse=True)
def _isolated_db():
    """Fresh temp DB for each test to avoid cross-test contamination."""
    tmpdir = tempfile.mkdtemp()
    set_db_path(os.path.join(tmpdir, "interview.db"))
    init_db()
    yield
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def mock_llm():
    """MockChatOpenAI patched into ``core.llm.get_llm`` and
    ``core.llm_client.get_llm`` (separate references after
    module-level import)."""
    mock = MockChatOpenAI()

    # Patch both import sites
    import core.llm as llm_mod
    import core.llm_client as llm_client_mod

    orig_llm = llm_mod.get_llm
    orig_client = llm_client_mod.get_llm

    llm_mod.get_llm = lambda *a, **kw: mock
    llm_client_mod.get_llm = lambda *a, **kw: mock

    yield mock

    llm_mod.get_llm = orig_llm
    llm_client_mod.get_llm = orig_client


@pytest.fixture
def orch(mock_llm):
    """Orchestrator wired to the mock LLM."""
    return InterviewOrchestrator(api_key="mock-key")


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Mock LLM unit tests
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestMockLLM:
    def test_invoke_returns_content(self):
        mock = MockChatOpenAI(default_response="hello world")
        msg = mock.invoke("any prompt")
        assert msg.content == "hello world"

    def test_stream_yields_chunks(self):
        mock = MockChatOpenAI(default_response="hello world", stream_chunk_size=3)
        chunks = list(mock.stream("p"))
        assert "".join(c.content for c in chunks) == "hello world"
        assert len(chunks) >= 3

    def test_response_matching_by_substring(self):
        mock = MockChatOpenAI(responses={"简历": "resume data", "评分": "score data"})
        assert mock.invoke("请分析简历").content == "resume data"
        assert mock.invoke("请进行评分").content == "score data"

    def test_no_match_falls_back_to_default(self):
        mock = MockChatOpenAI(default_response="fallback")
        assert mock.invoke("something else").content == "fallback"

    def test_call_history_tracked(self):
        mock = MockChatOpenAI()
        mock.invoke("first")
        mock.invoke("second")
        assert len(mock.call_history) == 2
        assert "second" in mock.last_prompt()

    def test_reset_clears_history(self):
        mock = MockChatOpenAI()
        mock.invoke("hello")
        mock.reset()
        assert len(mock.call_history) == 0

    def test_count_calls(self):
        mock = MockChatOpenAI()
        mock.invoke("a")
        list(mock.stream("b"))  # consume the generator
        assert mock.count_calls() == 2
        assert mock.count_calls("invoke") == 1
        assert mock.count_calls("stream") == 1

    def test_fail_on_prompt_raises(self):
        mock = MockChatOpenAI(fail_on_prompts=["PANIC"])
        with pytest.raises(RuntimeError, match="PANIC"):
            mock.invoke("this will PANIC now")

    def test_agent_uses_mock_through_get_llm(self, orch, mock_llm):
        """Verify the mock is plumbed through BaseAgent -> get_llm."""
        result = orch.interviewer.invoke("test prompt")
        assert result != ""
        assert mock_llm.count_calls() >= 1


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Resume analysis
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestResumeAnalysis:
    def test_analyze_writes_to_shared_memory(self, orch, mock_llm):
        mock_llm.responses["简历分析"] = json.dumps(
            {
                "tech_stack": ["Python", "PyTorch"],
                "level": "中级",
                "domains": ["NLP"],
                "gaps": ["分布式"],
                "highlights": ["RAG system"],
                "years_of_experience": 2,
            },
            ensure_ascii=False,
        )

        profile = orch.analyze_resume("Mock resume with Python and ML")
        assert profile is not None
        assert profile["level"] == "中级"
        assert "Python" in profile["tech_stack"]

        # Also in shared memory
        cached = orch.shared_memory.get("resume.profile")
        assert cached is not None
        assert cached["level"] == "中级"

    def test_empty_resume_returns_fallback(self, orch):
        profile = orch.analyze_resume("")
        # Orchestrator returns None for empty resume (no LLM call needed)
        assert profile is None
        # But it does write a fallback to shared memory
        fallback = orch.shared_memory.get("resume.profile")
        assert fallback is not None
        assert fallback["tech_stack"] == []

    def test_analysis_publishes_event(self, orch, mock_llm):
        events = []
        orch.message_bus.subscribe(Events.RESUME_ANALYZED, lambda m: events.append(m))
        orch.analyze_resume("Some resume")
        assert len(events) == 1
        assert events[0].source == "resume_analyst"


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Full interview lifecycle
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestInterviewLifecycle:
    def test_question_answer_evaluate(self, orch, mock_llm):
        orch.analyze_resume("Python, PyTorch, RAG experience")

        q = orch.generate_question("Transformer", stage_idx=0)
        assert q != ""
        assert mock_llm.count_calls("invoke") >= 1

        score, report, _needs_followup = orch.evaluate_answer(
            "test_user",
            "Transformer",
            q,
            "Self-Attention computes Q*K^T / sqrt(d_k) then softmax.",
            stage_idx=0,
        )
        assert isinstance(score, dict)
        assert "correctness" in score
        assert "depth" in score
        assert report != ""

        # Verify persisted to DB
        from backend.db.database import load_user

        records = load_user("test_user")
        assert len(records) >= 1

    def test_followup_triggered(self, orch, mock_llm):
        orch.analyze_resume("Beginner Python")

        q = orch.generate_question("LoRA", stage_idx=0)
        _score, _report, needs_followup = orch.evaluate_answer(
            "user",
            "LoRA",
            q,
            "I don't know much about LoRA.",
            stage_idx=0,
        )
        assert needs_followup is True

    def test_multi_stage_progression(self, orch, mock_llm):
        orch.analyze_resume("Senior engineer")

        history = []
        for stage_idx in range(3):
            q = orch.generate_question("Transformer", stage_idx=stage_idx, history=history)
            assert q != ""

            _score, _report, _needs_followup = orch.evaluate_answer(
                "user",
                "Transformer",
                q,
                f"Answer for stage {stage_idx}",
                stage_idx=stage_idx,
            )
            history.append({"q": q, "a": f"Answer for stage {stage_idx}"})
        assert len(history) == 3

    def test_report_generation_publishes_event(self, orch, mock_llm):
        questions = ["Q1", "Q2"]
        answers = ["A1", "A2"]
        scores = ["Score1", "Score2"]

        report = orch.generate_report(questions, answers, scores)
        assert report != ""
        assert len(report) > 20

        events = orch.message_bus.get_history(Events.REPORT_GENERATED)
        assert len(events) >= 1


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Error handling
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestErrorHandling:
    def test_bad_json_from_evaluator_triggers_fallback(self, orch, mock_llm):
        """When evaluator returns invalid JSON, orchestrator should
        return zero scores with a parse error flag."""
        orch.analyze_resume("test")

        # Make evaluator return non-JSON
        mock_llm.responses["评分"] = "这不是JSON，是纯文本！"

        q = orch.generate_question("Transformer", stage_idx=0)
        score, _report, _needs_followup = orch.evaluate_answer(
            "user",
            "Transformer",
            q,
            "Some answer",
            stage_idx=0,
        )
        assert score.get("_parse_error") is True
        assert score["correctness"] == 0
        assert score["depth"] == 0

    def test_short_answer_triggers_followup(self, orch, mock_llm):
        orch.analyze_resume("Test")

        q = orch.generate_question("Transformer", stage_idx=0)
        _score, _report, needs_followup = orch.evaluate_answer(
            "user",
            "Transformer",
            q,
            "Fine.",
            stage_idx=0,
        )
        assert needs_followup is True


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Agent communication (SharedMemory + MessageBus)
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestAgentCommunication:
    def test_resume_analyst_publishes_event(self, orch, mock_llm):
        received = []
        orch.message_bus.subscribe(Events.RESUME_ANALYZED, lambda m: received.append(m))
        orch.analyze_resume("Some resume")
        assert len(received) == 1

    def test_evaluator_publishes_event(self, orch, mock_llm):
        received = []
        orch.message_bus.subscribe(Events.ANSWER_EVALUATED, lambda m: received.append(m))
        orch.analyze_resume("test")
        q = orch.generate_question("Transformer", stage_idx=0)
        orch.evaluate_answer("u", "Transformer", q, "Answer", stage_idx=0)
        assert len(received) >= 1

    def test_shared_memory_updated_after_resume(self, orch, mock_llm):
        orch.analyze_resume("Python expert with ML background")
        assert orch.shared_memory.get("resume.profile") is not None
        assert orch.shared_memory.get("resume.level") is not None

    def test_agent_log_records_bus_events(self, orch, mock_llm):
        orch.analyze_resume("test resume")
        log = orch.get_agent_log()
        types = [e["type"] for e in log]
        assert Events.RESUME_ANALYZED in types


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Orchestrator helpers
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestOrchestratorHelpers:
    def test_agent_status_returns_all_roles(self, orch):
        statuses = dict(orch.agent_status())
        for role in ("简历分析师", "面试官", "评价官", "报告生成官"):
            assert role in statuses

    def test_reset_clears_everything(self, orch, mock_llm):
        orch.analyze_resume("test resume")
        assert orch.shared_memory.get("resume.profile") is not None
        orch.reset()
        assert orch.shared_memory.get("resume.profile") is None
        assert len(orch.get_agent_log()) == 0

    def test_get_shared_memory_snapshot(self, orch, mock_llm):
        orch.analyze_resume("some resume")
        snap = orch.get_shared_memory_snapshot()
        assert "resume.profile" in snap
        assert isinstance(snap["resume.profile"], str)
