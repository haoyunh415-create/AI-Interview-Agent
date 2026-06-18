"""Integration tests for the FastAPI backend API endpoints.

Uses FastAPI TestClient with mocked LLM to exercise the full request/response
cycle without needing real API keys or network access.
"""

import json
import os
import shutil
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.db.database import init_db, set_db_path
from backend.main import app
from core.mock_llm import MockChatOpenAI

client = TestClient(app)


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Fixtures
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
@pytest.fixture(autouse=True)
def _init():
    """Patch DB path and mock LLM for every test."""
    # Isolated temp DB
    tmpdir = tempfile.mkdtemp()
    set_db_path(os.path.join(tmpdir, "test_api.db"))
    init_db()

    mock = MockChatOpenAI()

    # Patch get_llm at the definition site + all import sites
    patch_targets = [
        "core.llm.get_llm",
        "core.llm_client.get_llm",
        "backend.api.chat.get_llm",
    ]
    patchers = [patch(t, return_value=mock) for t in patch_targets]
    for p in patchers:
        p.start()

    yield mock

    for p in reversed(patchers):
        p.stop()
    shutil.rmtree(tmpdir, ignore_errors=True)


def _clean_in_memory_sessions():
    """Clear the in-memory session store between tests."""
    from backend import session_store

    session_store._store.clear()


@pytest.fixture(autouse=True)
def _clean_sessions():
    _clean_in_memory_sessions()


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Auth
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestAuth:
    def test_register_and_login(self):
        # Register
        reg = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "password": "secret123",
                "display_name": "Test",
            },
        )
        assert reg.status_code == 200
        data = reg.json()
        assert "access_token" in data
        assert data["username"] == "testuser"

        # Login
        login = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "secret123",
            },
        )
        assert login.status_code == 200
        assert login.json()["access_token"] is not None

    def test_register_duplicate(self):
        client.post(
            "/api/auth/register",
            json={
                "username": "dupuser",
                "password": "secret123",
            },
        )
        resp = client.post(
            "/api/auth/register",
            json={
                "username": "dupuser",
                "password": "secret456",
            },
        )
        assert resp.status_code == 409

    def test_login_wrong_password(self):
        client.post(
            "/api/auth/register",
            json={
                "username": "user1",
                "password": "correctpw",
            },
        )
        resp = client.post(
            "/api/auth/login",
            json={
                "username": "user1",
                "password": "wrongpw",
            },
        )
        assert resp.status_code == 401

    def test_register_short_username(self):
        resp = client.post(
            "/api/auth/register",
            json={
                "username": "ab",
                "password": "secret123",
            },
        )
        assert resp.status_code == 400

    def test_register_short_password(self):
        resp = client.post(
            "/api/auth/register",
            json={
                "username": "validuser",
                "password": "12345",
            },
        )
        assert resp.status_code == 400

    def test_me_with_token(self):
        reg = client.post(
            "/api/auth/register",
            json={
                "username": "meuser",
                "password": "secret123",
            },
        )
        token = reg.json()["access_token"]

        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["username"] == "meuser"

    def test_me_without_token_returns_401(self):
        me = client.get("/api/auth/me")
        assert me.status_code == 401

    def test_me_with_bad_token(self):
        me = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert me.status_code == 401


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Health
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "active_sessions" in data

    def test_health_includes_version(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        version = resp.json()["version"]
        assert isinstance(version, str) and len(version) > 0
        assert version.count(".") == 2  # semver: X.Y.Z


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Chat
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestChat:
    def test_chat_works_without_api_key(self):
        """api_key is now optional — falls back to server env var or mock."""
        resp = client.post("/api/chat", json={"message": "hello"})
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data

    def test_chat_returns_reply(self):
        resp = client.post(
            "/api/chat",
            json={
                "message": "Hello",
                "api_key": "test-key",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data
        assert len(data["reply"]) > 0

    def test_chat_with_provider_model(self):
        resp = client.post(
            "/api/chat",
            json={
                "message": "Hi",
                "api_key": "test-key",
                "provider": "openai",
                "model": "gpt-4o",
            },
        )
        assert resp.status_code == 200
        assert "reply" in resp.json()


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Resume analysis
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestResume:
    def test_analyze_requires_text(self):
        resp = client.post(
            "/api/resume/analyze",
            json={
                "resume_text": "",
                "api_key": "test",
            },
        )
        assert resp.status_code == 400

    def test_analyze_returns_profile(self, _init):
        mock = _init
        mock.responses["简历分析"] = json.dumps(
            {
                "tech_stack": ["Python"],
                "level": "中级",
                "domains": ["NLP"],
                "gaps": [],
                "highlights": ["RAG"],
                "years_of_experience": 3,
                "keywords": [{"term": "Python", "weight": 0.9}],
            },
            ensure_ascii=False,
        )

        resp = client.post(
            "/api/resume/analyze",
            json={
                "resume_text": "Python developer with ML experience",
                "api_key": "test-key",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "profile" in data
        assert data["profile"]["level"] == "中级"


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Interview
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestInterview:
    def test_start_works_without_api_key(self):
        """api_key is now optional — falls back to server env var or mock."""
        resp = client.post(
            "/api/interview/start",
            json={
                "topic": "Transformer 核心",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data

    def test_start_returns_question(self, _init):
        resp = client.post(
            "/api/interview/start",
            json={
                "api_key": "test-key",
                "topic": "Transformer 核心",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "question" in data
        assert data["stage"] == "基础"
        assert data["stage_index"] == 0
        assert data["total_stages"] == 5
        assert data["is_followup"] is False

    def test_answer_returns_scores(self, _init):
        # Start first
        start_resp = client.post(
            "/api/interview/start",
            json={
                "api_key": "test-key",
                "topic": "Transformer 核心",
            },
        )
        sid = start_resp.json()["session_id"]

        # Answer
        resp = client.post(
            "/api/interview/answer",
            json={
                "session_id": sid,
                "answer": "Self-attention computes Q*K^T / sqrt(d_k) then softmax.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "score_text" in data
        assert "score_json" in data
        assert "needs_followup" in data
        assert "is_followup" in data
        assert "completed" in data

    def test_answer_stream_sse_format(self, _init):
        start_resp = client.post(
            "/api/interview/start",
            json={
                "api_key": "test-key",
                "topic": "Transformer 核心",
            },
        )
        sid = start_resp.json()["session_id"]

        resp = client.post(
            "/api/interview/answer/stream",
            json={
                "session_id": sid,
                "answer": "My detailed answer about transformers.",
            },
        )
        assert resp.status_code == 200
        # Should be SSE (StreamingResponse sets content-type)
        # TestClient returns the whole StreamingResponse body in resp.content
        body = resp.content
        assert body, "SSE response body should not be empty"

    def test_hint_returns_text(self, _init):
        start_resp = client.post(
            "/api/interview/start",
            json={
                "api_key": "test-key",
                "topic": "Transformer 核心",
            },
        )
        sid = start_resp.json()["session_id"]

        resp = client.post(
            "/api/interview/hint",
            json={
                "session_id": sid,
            },
        )
        assert resp.status_code == 200
        assert "hint" in resp.json()

    def test_report_requires_history(self, _init):
        """Report on session with no history should fail."""
        start_resp = client.post(
            "/api/interview/start",
            json={
                "api_key": "test-key",
                "topic": "Transformer 核心",
            },
        )
        sid = start_resp.json()["session_id"]

        resp = client.post(
            "/api/interview/report",
            json={
                "session_id": sid,
            },
        )
        assert resp.status_code == 400

    def test_nonexistent_session_returns_404(self):
        resp = client.post(
            "/api/interview/answer",
            json={
                "session_id": "doesnotexist",
                "answer": "test",
            },
        )
        assert resp.status_code == 404

    def test_start_with_custom_provider_model(self, _init):
        resp = client.post(
            "/api/interview/start",
            json={
                "api_key": "test-key",
                "topic": "Transformer 核心",
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["session_id"] is not None


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Bookmark CRUD
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestBookmarks:
    def test_create_and_list_bookmarks(self):
        # Create
        create_resp = client.post(
            "/api/bookmarks",
            json={
                "question": "What is RAG?",
                "answer": "Retrieval Augmented Generation",
                "topic": "RAG 鏋舵瀯",
            },
        )
        assert create_resp.status_code == 200
        assert "id" in create_resp.json()

        # List
        list_resp = client.get("/api/bookmarks?user=guest")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert len(data["bookmarks"]) >= 1

    def test_list_by_topic(self):
        client.post(
            "/api/bookmarks",
            json={
                "question": "Q1",
                "topic": "AI",
            },
        )
        client.post(
            "/api/bookmarks",
            json={
                "question": "Q2",
                "topic": "ML",
            },
        )

        resp = client.get("/api/bookmarks?user=guest&topic=AI")
        assert resp.status_code == 200
        data = resp.json()["bookmarks"]
        assert all(b["topic"] == "AI" for b in data)

    def test_delete_bookmark(self):
        create_resp = client.post(
            "/api/bookmarks",
            json={
                "question": "To be deleted",
            },
        )
        bm_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/api/bookmarks/{bm_id}?user=guest")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["ok"] is True

        # Verify gone
        list_resp = client.get("/api/bookmarks?user=guest")
        ids = [b["id"] for b in list_resp.json()["bookmarks"]]
        assert bm_id not in ids

    def test_check_bookmark(self):
        client.post(
            "/api/bookmarks",
            json={
                "question": "Unique question 12345",
            },
        )
        resp = client.get("/api/bookmarks/check?user=guest&question=Unique+question+12345")
        assert resp.status_code == 200
        assert resp.json()["bookmarked"] is True

        # Non-existing
        resp2 = client.get("/api/bookmarks/check?user=guest&question=nonexistent")
        assert resp2.json()["bookmarked"] is False


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Report
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestReport:
    def test_report_no_data_returns_404(self, _init):
        resp = client.post(
            "/api/report",
            json={
                "api_key": "test-key",
                "user": "guest",
            },
        )
        assert resp.status_code == 404

    def test_report_with_interview_data(self):
        start = client.post(
            "/api/interview/start",
            json={
                "api_key": "test-key",
                "topic": "Transformer 核心",
            },
        )
        sid = start.json()["session_id"]
        client.post(
            "/api/interview/answer",
            json={
                "session_id": sid,
                "answer": "Self-attention mechanism",
            },
        )

        resp = client.post(
            "/api/report",
            json={
                "api_key": "test-key",
                "user": "guest",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["total_questions"] >= 1
        assert "topic_scores" in data["stats"]
        assert "stage_scores" in data["stats"]

    def test_report_pdf_returns_file(self, _init):
        start = client.post(
            "/api/interview/start",
            json={
                "api_key": "test-key",
                "topic": "Transformer 核心",
            },
        )
        sid = start.json()["session_id"]
        client.post(
            "/api/interview/answer",
            json={
                "session_id": sid,
                "answer": "Multi-head attention",
            },
        )

        resp = client.post(
            "/api/report/pdf",
            json={
                "api_key": "test-key",
                "user": "guest",
            },
        )
        if resp.status_code != 200:
            print(f"PDF ERROR BODY: {resp.json()}")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"


# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?# Sessions
# 鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺?
class TestSessions:
    def test_list_sessions(self):
        resp = client.get("/api/sessions?user=guest")
        assert resp.status_code == 200
        data = resp.json()
        assert "sessions" in data

    def test_delete_nonexistent_session_returns_ok(self):
        resp = client.delete("/api/sessions/99999?user=guest")
        assert resp.status_code == 200
        assert resp.json()["ok"] is False

    def test_search_interviews_returns_results(self, _init):
        mock = _init
        from core.mock_llm import MockChatOpenAI

        if isinstance(mock, MockChatOpenAI):
            mock.default_response = "Test question about AI"

        # Start an interview & answer to create data
        start = client.post(
            "/api/interview/start",
            json={
                "api_key": "test-key",
                "topic": "Transformer 核心",
            },
        )
        sid = start.json()["session_id"]
        client.post(
            "/api/interview/answer",
            json={
                "session_id": sid,
                "answer": "A detailed answer about transformers.",
            },
        )

        # Search
        resp = client.get("/api/interviews/search?q=transformer&user=guest")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["total"] >= 1
