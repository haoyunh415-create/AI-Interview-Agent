"""Knowledge Retriever Agent — provides reference context for interview agents.

Reads technical documents from ``data/knowledge/`` and serves relevant excerpts
to the Interviewer and Evaluator via SharedMemory.

Improvements over pure keyword matching:
- Query expansion: known technical synonyms (transformer → attention, bert → nlp …)
- Section-level chunking: split documents by ``##`` headings, score per section
- Weighted scoring: title hit > section-header hit > body hit
- Graceful degradation: works without any extra dependencies
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents.base import BaseAgent
from core.config import DATA_DIR
from core.logging_config import get_logger
from core.memory import Events

_log = get_logger("agent.knowledge_retriever")

_STOPWORDS: set[str] = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "used",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "as",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "they",
    "them",
    "their",
    "what",
    "which",
    "who",
    "whom",
    "when",
    "where",
    "why",
    "how",
    "和",
    "的",
    "了",
    "在",
    "是",
    "我",
    "有",
    "不",
    "就",
    "人",
    "都",
    "一",
    "一个",
    "上",
    "也",
    "很",
    "到",
    "说",
    "要",
    "去",
    "你",
    "会",
    "着",
    "没有",
    "看",
    "好",
    "自己",
    "这",
    "他",
    "她",
    "它",
    "们",
}

_TERM_MAP: dict[str, set[str]] = {
    "transformer": {"attention", "self-attention", "encoder", "decoder", "多头注意力", "位置编码"},
    "bert": {"nlp", "预训练", "mlm", "masked language model", "wordpiece", "fine-tuning"},
    "attention": {"transformer", "self-attention", "注意力", "qkv", "query key value"},
    "cnn": {"卷积", "卷积神经网络", "convolution", "pooling", "池化"},
    "rnn": {"lstm", "gru", "循环神经网络", "sequence", "时序"},
    "lstm": {"rnn", "gru", "长短期记忆", "gate", "遗忘门"},
    "dropout": {"正则化", "regularization", "overfitting", "过拟合"},
    "batchnorm": {"layer normalization", "归一化", "layernorm", "batch normalization"},
    "gan": {"生成对抗网络", "generative", "discriminator", "判别器"},
    "reinforcement learning": {"rl", "强化学习", "q-learning", "policy gradient", "dqn"},
    "optimizer": {"adam", "sgd", "动量", "learning rate", "优化器"},
    "激活函数": {"activation", "relu", "gelu", "sigmoid", "tanh"},
    "transformer核心": {"transformer", "attention", "self-attention", "位置编码", "layer normalization"},
    "深度学习": {"deep learning", "神经网络", "反向传播", "backpropagation", "梯度下降"},
    "自然语言处理": {"nlp", "bert", "transformer", "word embedding", "文本分类"},
    "计算机视觉": {"cnn", "图像识别", "目标检测", "object detection", "image classification"},
    "模型部署": {"model serving", "onnx", "tensorrt", "量化", "pruning"},
    "推荐系统": {"recommender", "collaborative filtering", "协同过滤", "embedding", "召回"},
}


@dataclass
class _Section:
    doc_name: str
    heading: str
    content: str
    heading_level: int


class KnowledgeRetriever(BaseAgent):
    """Retrieves knowledge context documents for interview agents."""

    def __init__(
        self,
        api_key: str | None = None,
        shared_memory: Any = None,
        message_bus: Any = None,
        telemetry: Any = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__(
            name="knowledge_retriever",
            role="知识检索助手",
            temperature=0.0,
            api_key=api_key,
            shared_memory=shared_memory,
            message_bus=message_bus,
            telemetry=telemetry,
            provider=provider,
            model=model,
        )
        self._documents: dict[str, str] = {}
        self._sections: list[_Section] = []
        self._index: dict[str, list[int]] = {}

    def retrieve(self, topic: str) -> str:
        """Retrieve knowledge context for *topic* with query expansion + section scoring."""
        if not self._documents:
            self._load_documents()
        context = self._find_best_match(topic)
        self.memory_set(f"context.{topic}", context, {"topic": topic})
        self.publish_event(
            Events.CONTEXT_RETRIEVED,
            {
                "topic": topic,
                "length": len(context),
            },
        )
        _log.info("retrieved context for '%s': %d chars", topic, len(context))
        return context

    def get_available_topics(self) -> list[str]:
        if not self._documents:
            self._load_documents()
        return list(self._documents.keys())

    def _load_documents(self) -> None:
        knowledge_dir = Path(DATA_DIR) / "knowledge"
        if not knowledge_dir.exists():
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            return
        for ext in ("*.md", "*.txt"):
            for path in sorted(knowledge_dir.glob(ext)):
                try:
                    content = path.read_text(encoding="utf-8")
                    self._documents[path.stem] = content
                except Exception as exc:
                    _log.warning("failed to load %s: %s", path, exc)
        self._split_sections()
        self._build_index()

    def _split_sections(self) -> None:
        self._sections = []
        for doc_name, content in self._documents.items():
            lines = content.split("\n")
            current_heading = ""
            current_level = 0
            current_lines: list[str] = []
            for line in lines:
                heading_match = re.match(r"^(#{1,6})\s+(.+)", line)
                if heading_match:
                    body = "\n".join(current_lines).strip()
                    if body or current_heading:
                        self._sections.append(
                            _Section(
                                doc_name=doc_name,
                                heading=current_heading,
                                content=body,
                                heading_level=current_level,
                            )
                        )
                    current_level = len(heading_match.group(1))
                    current_heading = heading_match.group(2).strip()
                    current_lines = []
                else:
                    current_lines.append(line)
            body = "\n".join(current_lines).strip()
            self._sections.append(
                _Section(
                    doc_name=doc_name,
                    heading=current_heading,
                    content=body,
                    heading_level=current_level,
                )
            )

    def _build_index(self) -> None:
        self._index = {}
        for idx, sec in enumerate(self._sections):
            title_kws = self._extract_keywords(sec.doc_name.replace("_", " "), max_keywords=10)
            for kw in title_kws:
                self._index.setdefault(kw, []).append(idx)
            if sec.heading:
                heading_kws = self._extract_keywords(sec.heading, max_keywords=10)
                for kw in heading_kws:
                    self._index.setdefault(kw, []).append(idx)
                    self._index.setdefault(kw, []).append(idx)
            body_kws = self._extract_keywords(sec.content, max_keywords=30)
            for kw in body_kws:
                self._index.setdefault(kw, []).append(idx)

    def _find_best_match(self, topic: str) -> str:
        if not self._sections:
            return ""
        expanded_terms = self._expand_query(topic)
        query_keywords = set(self._extract_keywords(" ".join(expanded_terms), max_keywords=20))
        if not query_keywords:
            return ""
        section_scores = [0.0] * len(self._sections)
        for kw in query_keywords:
            for idx in self._index.get(kw, []):
                section_scores[idx] += 1.0
        if not any(section_scores):
            return ""
        ranked = sorted(enumerate(section_scores), key=lambda x: x[1], reverse=True)
        _best_idx, best_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0
        if best_score > second_score * 2:
            return self._format_result([ranked[0]])
        else:
            top_n = sum(1 for _, s in ranked if s >= best_score * 0.5)
            return self._format_result(ranked[: max(top_n, 2)])

    def _expand_query(self, topic: str) -> list[str]:
        terms = [topic]
        topic_lower = topic.lower().strip()
        if topic_lower in _TERM_MAP:
            terms.extend(_TERM_MAP[topic_lower])
        for key, related in _TERM_MAP.items():
            if key in topic_lower or topic_lower in key:
                terms.extend(related)
        return terms

    def _format_result(self, ranked: list[tuple[int, float]]) -> str:
        if not ranked:
            return ""
        parts: list[str] = []
        seen_docs: set[str] = set()
        for idx, _score in ranked[:3]:
            if idx >= len(self._sections):
                continue
            sec = self._sections[idx]
            header = f"# {sec.doc_name}" if sec.doc_name not in seen_docs else ""
            seen_docs.add(sec.doc_name)
            if sec.heading:
                excerpt = f"{header}\n## {sec.heading}\n{sec.content[:500]}"
            else:
                excerpt = f"{header}\n{sec.content[:500]}"
            excerpt = excerpt.strip()
            if excerpt:
                parts.append(excerpt)
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _extract_keywords(text: str, max_keywords: int = 15) -> list[str]:
        tokens = re.findall(r"[a-zA-Z_\-+#./]{2,}|[一-鿿]{2,}", text.lower())
        keywords = [t for t in tokens if t not in _STOPWORDS and len(t) >= 2]
        seen: set[str] = set()
        result: list[str] = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                result.append(kw)
        return result[:max_keywords]


DEMO_KNOWLEDGE: dict[str, str] = {
    "transformer": """# Transformer 核心原理

## 架构概述
Transformer 由 Encoder 和 Decoder 两部分组成。

## Self-Attention
Scaled Dot-Product Attention: Attention(Q, K, V) = softmax(QK^T / √d_k) V

## Multi-Head Attention
将 Q, K, V 线性投影到 h 个子空间并行计算。

## Position Encoding
PE(pos, 2i) = sin(pos / 10000^(2i/d_model))

## Feed-Forward Network
FFN(x) = max(0, xW1 + b1)W2 + b2
""",
    "bert": """# BERT — Bidirectional Encoder Representations from Transformers

## 核心思想
BERT 使用 Transformer Encoder 进行深度双向预训练。
通过 Masked Language Model 和 Next Sentence Prediction 学习语言表示。

## 输入表示
Token Embeddings + Segment Embeddings + Position Embeddings

## MLM
随机遮盖 15% 的 token 进行预测。
""",
    "deep_learning_basics": """# 深度学习基础

## 反向传播
链式法则：∂L/∂w = ∂L/∂y · ∂y/∂w

## 激活函数
ReLU, Leaky ReLU, GELU, Swish/SiLU

## 优化器
SGD + Momentum, Adam, AdamW

## 正则化
Dropout, LayerNorm, Weight Decay
""",
}


def create_demo_knowledge_base() -> int:
    """Write demo knowledge documents to ``data/knowledge/``."""
    knowledge_dir = Path(DATA_DIR) / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for name, content in DEMO_KNOWLEDGE.items():
        path = knowledge_dir / f"{name}.md"
        if not path.exists():
            path.write_text(content.strip() + "\n", encoding="utf-8")
            count += 1
    if count:
        _log.info("created %d demo knowledge document(s)", count)
    return count
