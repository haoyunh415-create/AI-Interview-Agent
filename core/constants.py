"""Centralized constants: interview stages, topic mappings, and keywords.

Putting all string constants in one place prevents:
- Typo bugs from scattered magic strings
- Rename pain when keys need to change
- Cross-module import coupling via raw strings
"""

# ═══════════════════════════════════════════════
# Interview stages
# ═══════════════════════════════════════════════

STAGES = ["基础", "原理", "进阶", "项目", "挑战"]


# ═══════════════════════════════════════════════
# Topic mapping (display name → internal topic)
# ═══════════════════════════════════════════════

TOPIC_MAP: dict[str, str] = {
    "Transformer 核心": "Transformer核心原理",
    "RAG 架构": "RAG检索增强生成",
    "模型微调": "模型微调技术",
    "大模型评估": "大模型综合评估",
    "自定义岗位": "自定义岗位",
    "深度学习基础": "深度学习基础",
    "自然语言处理": "自然语言处理",
    "计算机视觉": "计算机视觉",
    "强化学习": "强化学习",
    "模型部署与优化": "模型部署与优化",
    "推荐系统": "推荐系统",
    "自定义": "自定义",
}

INTERNAL_TO_DISPLAY: dict[str, str] = {v: k for k, v in TOPIC_MAP.items()}

# ── Topic keywords (for interview question guidance) ──

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "Transformer核心原理": [
        "self-attention",
        "multi-head",
        "encoder-decoder",
        "positional encoding",
        "transformer架构",
    ],
    "RAG检索增强生成": [
        "retrieval",
        "vector database",
        "chunk",
        "embedding",
        "rag架构",
        "rag优化",
    ],
    "模型微调技术": [
        "lora",
        "fine-tuning",
        "prefix-tuning",
        "adapter",
        "参数高效微调",
    ],
    "大模型综合评估": [
        "llm评估",
        "benchmark",
        "幻觉",
        "rlhf",
        "模型压缩",
        "推理优化",
    ],
    "深度学习基础": [
        "反向传播",
        "梯度消失",
        "激活函数",
        "正则化",
        "batch normalization",
        "dropout",
        "优化器",
    ],
    "自然语言处理": [
        "word embedding",
        "transformer",
        "bert",
        "gpt",
        "seq2seq",
        "attention",
        "分词",
    ],
    "计算机视觉": [
        "cnn",
        "卷积",
        "目标检测",
        "图像分割",
        "resnet",
        "yolo",
        "数据增强",
    ],
    "强化学习": [
        "q-learning",
        "policy gradient",
        "dqn",
        "ppo",
        "reward",
        "马尔可夫决策",
    ],
    "模型部署与优化": [
        "模型量化",
        "蒸馏",
        "onnx",
        "tensorrt",
        "推理加速",
        "模型压缩",
        "服务部署",
    ],
    "推荐系统": [
        "协同过滤",
        "矩阵分解",
        "widedeep",
        "召回",
        "排序",
        "特征工程",
        "冷启动",
    ],
}


def get_topic_keywords(topic: str) -> list[str]:
    """Return configured keywords for an interview topic."""
    return TOPIC_KEYWORDS.get(topic, [])
