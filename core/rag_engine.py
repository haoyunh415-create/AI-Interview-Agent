"""Stub RAG engine — kept for backward compatibility.

All actual retrieval is handled by KnowledgeRetriever agent directly.
"""

from core.logging_config import get_logger

_log = get_logger("rag")


def retrieve(query: str, k: int = 3) -> list[str]:
    """Stub: returns empty results."""
    return []


def retrieve_with_metadata(query: str, k: int = 3) -> list[dict]:
    """Stub: returns empty results."""
    return []


def rag_query(query: str, k: int = 3) -> str:
    """Stub: returns empty string."""
    return ""
