"""MockChatOpenAI — a drop-in replacement for langchain_openai.ChatOpenAI.

Provides realistic canned responses, call tracking, and error simulation
so tests can exercise the full agent pipeline without network calls or
API keys.

Usage in tests (conftest.py)::

    from core.mock_llm import MockChatOpenAI

    @pytest.fixture(autouse=True)
    def _mock_llm(monkeypatch):
        mock = MockChatOpenAI(responses={
            "简历分析": '{"tech_stack": ["Python"], "level": "中级", ...}',
        })
        monkeypatch.setattr("core.llm.get_llm", lambda **kw: mock)
"""

import json
from collections.abc import Iterator
from typing import Any

# ═══════════════════════════════════════════════════════
# Duck-typed message objects (no langchain dependency)
# ═══════════════════════════════════════════════════════


class MockAIMessage:
    """Duck-typed replacement for ``langchain_core.messages.AIMessage``."""

    def __init__(self, content: str = "") -> None:
        self.content = content

    def __repr__(self) -> str:
        return f"MockAIMessage(content={self.content[:60]!r}...)"


class MockAIMessageChunk:
    """Duck-typed replacement for ``langchain_core.messages.AIMessageChunk``."""

    def __init__(self, content: str = "") -> None:
        self.content = content

    def __repr__(self) -> str:
        return f"MockAIMessageChunk(content={self.content[:60]!r}...)"


# ═══════════════════════════════════════════════════════
# Default responses for interview scenarios
# ═══════════════════════════════════════════════════════

DEFAULT_RESPONSES: dict[str, str] = {
    "简历分析": json.dumps(
        {
            "tech_stack": ["Python", "PyTorch", "LangChain"],
            "level": "中级",
            "domains": ["NLP", "RAG"],
            "gaps": ["分布式系统", "MLOps"],
            "highlights": ["构建了基于RAG的问答系统"],
            "years_of_experience": 2,
        },
        ensure_ascii=False,
    ),
    "评分": json.dumps(
        {
            "correctness": 7,
            "logic": 6,
            "depth": 5,
            "expression": 8,
            "summary": "基础概念掌握较好，但深度不够",
            "improvement": "建议深入理解Transformer原理",
            "needs_followup": True,
            "followup_reason": "回答缺少具体实现细节",
        },
        ensure_ascii=False,
    ),
    "追问": "你刚才提到了注意力机制，能具体说说在实现Multi-Head Attention时，为什么需要做线性变换吗？",
    "出题": "请解释Transformer中的Self-Attention机制是如何计算的，并说明它为什么比RNN更适合处理长序列？",
    "提示": "试试用 Query-Key-Value 的角度来思考",
    "报告": (
        "## 面试总结报告\n\n"
        "### 整体评价：良好\n\n"
        "候选人在基础概念方面表现扎实，但在深度理解上还有提升空间。\n\n"
        "### 主要优点\n"
        "1. 对Transformer架构有基本理解\n"
        "2. 表达能力较好\n\n"
        "### 需要加强\n"
        "1. 建议深入理解Self-Attention的数学原理\n"
        "2. 建议多关注工程实践\n"
    ),
    "生成问题": (
        "1. 请解释Transformer的Encoder-Decoder结构\n"
        "2. 为什么需要位置编码？\n"
        "3. 解释Masked Self-Attention的作用\n"
        "4. 如何优化推理速度？\n"
        "5. 对比不同模型的优缺点"
    ),
}


# ═══════════════════════════════════════════════════════
# MockChatOpenAI
# ═══════════════════════════════════════════════════════


class MockChatOpenAI:
    """In-process mock of ``langchain_openai.ChatOpenAI``.

    Parameters
    ----------
    responses : dict[str, str], optional
        Map of prompt-substring → canned response.  The first key that
        appears in the prompt wins.  Falls back to *default_response*.
    default_response : str
        Used when no response key matches.
    json_mode : bool
        If True, wrap non-JSON responses in a JSON envelope so
        ``BaseAgent.invoke_json`` can parse them.  (You usually want to
        provide proper JSON responses instead.)
    stream_chunk_size : int
        Characters per chunk when streaming.
    fail_on_prompts : list[str], optional
        Substrings that should trigger a ``RuntimeError`` (to simulate
        API failures).
    use_defaults : bool
        If True (default), pre-populate responses with DEFAULT_RESPONSES.
        Set to False when you need full control over mock responses
        (prevents accidental key collisions with prompt substrings).
    """

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        default_response: str = "Mock LLM response",
        json_mode: bool = False,
        stream_chunk_size: int = 20,
        fail_on_prompts: list[str] | None = None,
        use_defaults: bool = True,
    ) -> None:
        self.responses = {
            **(DEFAULT_RESPONSES if use_defaults else {}),
            **(responses or {}),
        }
        self.default_response = default_response
        self.json_mode = json_mode
        self.stream_chunk_size = stream_chunk_size
        self.fail_on_prompts = fail_on_prompts or []

        # ── Observability ──
        self.call_history: list[dict[str, Any]] = []
        self._call_count = 0

    # ── Public API (matches ChatOpenAI) ──

    def invoke(self, prompt: str) -> MockAIMessage:
        self._record_call("invoke", prompt)
        resp = self._resolve_response(prompt)
        return MockAIMessage(content=resp)

    def stream(self, prompt: str) -> Iterator[MockAIMessageChunk]:
        self._record_call("stream", prompt)
        resp = self._resolve_response(prompt)
        return self._chunk_iter(resp, self.stream_chunk_size)

    @staticmethod
    def _chunk_iter(text: str, size: int) -> Iterator[MockAIMessageChunk]:
        for i in range(0, len(text), size):
            yield MockAIMessageChunk(content=text[i : i + size])

    # ── Test helpers ──

    def reset(self) -> None:
        """Clear call history and counter."""
        self.call_history.clear()
        self._call_count = 0

    def last_prompt(self) -> str | None:
        """Return the most recent prompt, useful for assertion."""
        if self.call_history:
            return self.call_history[-1]["prompt"]
        return None

    def count_calls(self, method: str | None = None) -> int:
        """Count invocations, optionally filtered by method type."""
        if method:
            return sum(1 for c in self.call_history if c["method"] == method)
        return len(self.call_history)

    # ── Internal ──

    def _resolve_response(self, prompt: str) -> str:
        self._check_failures(prompt)

        for key, response in self.responses.items():
            if key in prompt:
                return response

        if self.json_mode and not self.default_response.startswith("{"):
            return json.dumps({"content": self.default_response}, ensure_ascii=False)

        return self.default_response

    def _check_failures(self, prompt: str) -> None:
        for trigger in self.fail_on_prompts:
            if trigger in prompt:
                raise RuntimeError(f"MockChatOpenAI simulated failure triggered by {trigger!r}")

    def _record_call(self, method: str, prompt: str) -> None:
        self._call_count += 1
        self.call_history.append(
            {
                "n": self._call_count,
                "method": method,
                "prompt": prompt[:200],
                "prompt_len": len(prompt),
            }
        )

    def __repr__(self) -> str:
        return f"<MockChatOpenAI calls={self._call_count} >"
