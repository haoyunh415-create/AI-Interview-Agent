"""Backward-compatible wrappers that delegate to the multi-agent system.

All public functions preserve their original signatures so existing callers
(app.py) work with minimal changes.
"""

import time

from agents.evaluator import Evaluator
from agents.interviewer import Interviewer
from agents.orchestrator import InterviewOrchestrator
from agents.report_writer import ReportWriter
from core.logging_config import get_logger, log_duration

_log = get_logger("interview")

# Re-exported constants

TOPICS = {
    "Transformer核心原理": [
        "self-attention",
        "multi-head",
        "encoder-decoder",
        "positional encoding",
        "transformer架构",
    ],
    "RAG检索增强生成": ["retrieval", "vector database", "chunk", "embedding", "rag架构", "rag优化"],
    "模型微调技术": ["lora", "fine-tuning", "prefix-tuning", "adapter", "参数高效微调"],
    "大模型综合评估": ["llm评估", "benchmark", "幻觉", "rlhf", "模型压缩", "推理优化"],
}

STAGE_EMPHASIS = {
    "基础": "重点评估对概念的理解准确性",
    "原理": "重点评估对底层机制的解释能力",
    "进阶": "重点评估解决复杂问题的思路",
    "项目": "重点评估实践经验和工程能力",
    "挑战": "重点评估创新思维和深度洞察",
}

CUSTOM_JOB_PROMPT = """你是一位资深的技术面试官。请根据以下岗位描述，生成针对性的面试问题。

岗位描述：
{job_description}

要求：
1. 生成5个针对该岗位的核心技术问题
2. 覆盖基础知识、原理理解、实践经验
3. 问题要具体且能考察真实能力

直接输出问题列表："""


# Singleton orchestrator
_orchestrator = None
_last_api_key = None


def _get_orchestrator(api_key=None):
    global _orchestrator, _last_api_key
    if _orchestrator is None or _last_api_key != api_key:
        _log.info("creating new orchestrator")
        _orchestrator = InterviewOrchestrator(api_key)
        _last_api_key = api_key
    return _orchestrator


def reset_orchestrator():
    global _orchestrator
    _log.info("resetting orchestrator")
    _orchestrator = None


# ── Public API ──


def get_topic_keywords(topic):
    return TOPICS.get(topic, [])


def generate_custom_questions(job_description, api_key=None):
    prompt = CUSTOM_JOB_PROMPT.format(job_description=job_description)
    interviewer = Interviewer(api_key)
    response = interviewer.invoke(prompt)
    questions = [
        q.strip()
        for q in response.split("\n")
        if q.strip() and (q[0].isdigit() or q.startswith("-") or q.startswith("*"))
    ]
    if not questions:
        questions = [q.strip() for q in response.split("\n") if len(q.strip()) > 10]
    return questions[:5]


def generate_custom_questions_stream(job_description, api_key=None):
    """Streaming variant: yield question tokens as they generate."""
    prompt = CUSTOM_JOB_PROMPT.format(job_description=job_description)
    interviewer = Interviewer(api_key)
    yield from interviewer.invoke_stream(prompt)


def get_hints(question, api_key=None):
    interviewer = Interviewer(api_key)
    return interviewer.generate_hint(question)


def get_hints_stream(question, api_key=None):
    """Streaming variant: yield hint tokens."""
    interviewer = Interviewer(api_key)
    yield from interviewer.invoke_stream(
        "基于这个问题，给考生一个简短的提示（10字以内），帮助他们理清答题方向。\n"
        f"问题：{question}\n"
        "只输出一个简洁的提示，不要多余内容：\n",
        temperature=0.3,
    )


def evaluate(question, answer, stage, api_key=None):
    evaluator = Evaluator(api_key)
    return evaluator.evaluate(question, answer, stage)


def generate_summary(questions, answers, scores, api_key=None):
    writer = ReportWriter(api_key)
    return writer.generate_summary(questions, answers, scores)


def generate_summary_stream(questions, answers, scores, profile=None, api_key=None):
    """Streaming variant: yield summary tokens."""
    writer = ReportWriter(api_key)
    yield from writer.generate_summary_stream(questions, answers, scores, profile)


def step(
    user,
    topic,
    context,
    idx,
    question=None,
    answer=None,
    history=None,
    resume=None,
    custom_questions=None,
    api_key=None,
):
    """Run one step of the interview. Returns a dict with full state."""
    orch = _get_orchestrator(api_key)
    t0 = time.monotonic()

    if resume:
        orch.analyze_resume(resume)
    if not orch._context:
        orch.fetch_context(topic)

    result = orch.step(user, topic, idx, question, answer, history, resume, custom_questions)
    log_duration(_log, f"step (stage={idx}, is_answer={answer is not None})", t0)
    return result
