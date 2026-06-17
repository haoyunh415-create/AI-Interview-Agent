"""Chat context window management — sliding window + smart truncation.

Prevents LLM context overflow by keeping only the most relevant messages
and compressing/removing old ones when the token budget is exceeded.
"""

from __future__ import annotations

# Rough token estimation: 1 token ≈ 4 chars for English, ≈ 2 chars for Chinese
_CHARS_PER_TOKEN = 3.5
_MAX_CONTEXT_TOKENS = 128_000  # default max for most LLMs
_MAX_RESPONSE_TOKENS = 4_000
_SYSTEM_TOKEN_COUNT = 100  # system prompt overhead


def estimate_tokens(text: str) -> int:
    """Rough token count estimation (character-based)."""
    if not text:
        return 0
    # Chinese chars (~2 per token), others (~4 per token)
    chinese_count = sum(1 for c in text if "一" <= c <= "鿿")
    other_count = len(text) - chinese_count
    return max(1, int(chinese_count / 2 + other_count / 4))


def estimate_message_tokens(msg: dict[str, str]) -> int:
    """Estimate tokens for a single message dict with role + content."""
    return estimate_tokens(msg.get("content", ""))


def truncate_messages(
    messages: list[dict[str, str]],
    system_prompt: str = "",
    max_tokens: int = _MAX_CONTEXT_TOKENS - _MAX_RESPONSE_TOKENS - _SYSTEM_TOKEN_COUNT,
    keep_recent: int = 6,
) -> list[dict[str, str]]:
    """Truncate messages to fit within the token budget.

    Strategy:
    1. Always keep the system message (if any)
    2. Keep the last ``keep_recent`` messages (most relevant)
    3. If still over budget, remove middle messages oldest-first
    4. If still over budget, truncate the earliest remaining message

    Args:
        messages: List of message dicts with ``role`` and ``content`` keys.
        system_prompt: Optional system prompt text (counted separately).
        max_tokens: Maximum tokens for the messages portion.
        keep_recent: Number of most recent messages to always preserve.

    Returns:
        Truncated message list.
    """
    if not messages:
        return []

    # Build result with system prompt
    result = list(messages)

    # Check if we're within budget
    total = estimate_messages_tokens(result)
    if total <= max_tokens:
        return result

    # Strategy 1: Keep last N messages, discard oldest
    if len(result) > keep_recent:
        result = result[-keep_recent:]
        total = estimate_messages_tokens(result)

    # Strategy 2: Truncate earliest message content if still over
    if total > max_tokens and result:
        budget_per_msg = max_tokens // max(len(result), 1)
        for i, msg in enumerate(result):
            content = msg.get("content", "")
            token_count = estimate_tokens(content)
            if token_count > budget_per_msg:
                # Truncate to budget
                target_chars = int(budget_per_msg * _CHARS_PER_TOKEN)
                result[i] = {
                    **msg,
                    "content": content[:target_chars] + f"\n\n[... 内容已截断，原始约 {token_count} tokens]",
                }

    return result


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    """Total token count for a list of messages."""
    return sum(estimate_message_tokens(m) for m in messages)


def auto_truncate_for_llm(
    messages: list[dict[str, str]],
    max_tokens: int = _MAX_CONTEXT_TOKENS,
    reserve_ratio: float = 0.85,
) -> list[dict[str, str]]:
    """Auto-truncate message list to fit LLM context window.

    Convenience wrapper that:
    1. Reserves ``reserve_ratio`` of the window for messages
    2. Applies sliding window + content truncation

    Args:
        messages: Full message history.
        max_tokens: LLM max context window.
        reserve_ratio: Fraction of window to use for messages (rest for response).

    Returns:
        Truncated message list safe to send to the LLM.
    """
    available = int(max_tokens * reserve_ratio)
    return truncate_messages(messages, max_tokens=available)
