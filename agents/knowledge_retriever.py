from agents.base import BaseAgent
from core.rag_engine import retrieve, retrieve_with_metadata, rag_query
from core.config import RETRIEVAL_SCORE_THRESHOLD
from core.logging_config import get_logger

_log = get_logger("agent.knowledge_retriever")

KNOWLEDGE_RETRIEVER_ROLE = """你是一位知识检索官（Knowledge Retriever Agent）。
你的职责是从知识库中检索最相关的内容，为面试官和评价官提供参考依据。

你拥有以下工具：
1. 语义搜索：基于向量相似度检索知识库
2. 关键词匹配：对英文技术术语做加权匹配
3. RAG查询：检索+AI生成综合答案"""


class KnowledgeRetriever(BaseAgent):
    """Retrieves knowledge from the vector database for other agents."""

    def __init__(self, api_key=None):
        super().__init__(
            name="knowledge_retriever",
            role=KNOWLEDGE_RETRIEVER_ROLE,
            temperature=0.0,
            api_key=api_key,
        )

    def search(self, query, threshold=RETRIEVAL_SCORE_THRESHOLD):
        """Simple retrieval: return best matching text."""
        try:
            return retrieve(query, threshold)
        except FileNotFoundError:
            return ""

    def search_with_meta(self, query, threshold=RETRIEVAL_SCORE_THRESHOLD):
        """Retrieval with metadata: return content + score + source."""
        try:
            return retrieve_with_metadata(query, threshold)
        except FileNotFoundError:
            return None

    def search_and_answer(self, query):
        """RAG query: retrieve + generate answer."""
        try:
            answer, sources = rag_query(query, self._api_key)
            return answer, sources
        except FileNotFoundError:
            return "知识库未初始化，请先构建索引。", []

    def get_topic_context(self, topic):
        """Get knowledge context for a given interview topic."""
        result = self.search(topic)
        _log.info("topic=%s len=%d", topic, len(result) if result else 0)
        return result
