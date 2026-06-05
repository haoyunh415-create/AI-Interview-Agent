"""Tests for chat context window management."""

from core.chat_context import (
    auto_truncate_for_llm,
    estimate_tokens,
    truncate_messages,
)


class TestEstimateTokens:
    def test_empty(self):
        assert estimate_tokens("") == 0

    def test_english(self):
        # ~4 chars per token
        text = "hello world " * 100  # 1200 chars
        tokens = estimate_tokens(text)
        assert 250 < tokens < 400

    def test_chinese(self):
        # ~2 chars per token
        text = "你好世界 " * 100
        tokens = estimate_tokens(text)
        assert 150 < tokens < 350


class TestTruncateMessages:
    def test_empty_list(self):
        assert truncate_messages([]) == []

    def test_within_budget(self):
        msgs = [{"role": "user", "content": "hi"}]
        result = truncate_messages(msgs, max_tokens=10_000)
        assert len(result) == 1

    def test_truncates_oldest(self):
        msgs = [{"role": "user", "content": f"Msg{i} " + "x" * 300} for i in range(20)]
        result = truncate_messages(msgs, max_tokens=600, keep_recent=3)
        # Should keep only a subset — not all 20
        assert len(result) < 15
        # The very last message should be kept
        assert any("Msg19" in m["content"] for m in result)

    def test_content_truncation(self):
        long_content = "A" * 10_000
        msgs = [{"role": "user", "content": long_content}]
        result = truncate_messages(msgs, max_tokens=100)
        assert len(result) == 1
        assert len(result[0]["content"]) < len(long_content)
        assert "内容已截断" in result[0]["content"]


class TestAutoTruncate:
    def test_preserves_recent(self):
        msgs = [
            {"role": "user", "content": "old question"},
            {"role": "assistant", "content": "old answer"},
            {"role": "user", "content": "new question"},
        ]
        result = auto_truncate_for_llm(msgs, max_tokens=50_000)
        assert len(result) >= 2
