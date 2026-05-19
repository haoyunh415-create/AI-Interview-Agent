"""Backward-compatible wrappers that delegate to the multi-agent system.

All public functions preserve their original signatures so existing callers
(app.py) work with minimal changes.
"""

import json
from agents.orchestrator import InterviewOrchestrator, STAGES
from agents.interviewer import Interviewer, get_level_bias
from agents.evaluator import Evaluator, MAX_FOLLOWUPS_PER_STAGE
from agents.report_writer import ReportWriter

# ── Re-exported constants ──
# STAGES, MAX_FOLLOWUPS_PER_STAGE imported above

TOPICS = {
    "Transformer核心原理": ["self-attention", "multi-head", "encoder-decoder", "positional encoding", "transformer架构"],
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


# ── Singleton orchestrator ──
_orchestrator = None
_last_api_key = None


def _get_orchestrator(api_key=None):
    global _orchestrator, _last_api_key
    if _orchestrator is None or _last_api_key != api_key:
        _orchestrator = InterviewOrchestrator(api_key)
        _last_api_key = api_key
    return _orchestrator


def reset_orchestrator():
    global _orchestrator
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


def get_hints(question, api_key=None):
    interviewer = Interviewer(api_key)
    return interviewer.generate_hint(question)


def evaluate(question, answer, stage, api_key=None):
    evaluator = Evaluator(api_key)
    return evaluator.evaluate(question, answer, stage)


def generate_summary(questions, answers, scores, api_key=None):
    writer = ReportWriter(api_key)
    return writer.generate_summary(questions, answers, scores)


def step(user, topic, context, idx, question=None, answer=None, history=None, resume=None, custom_questions=None, api_key=None):
    """Run one step of the interview. Returns a dict with full state.

    When answer is None (starting):
        {"question": str, "stage_idx": int, "is_followup": False}

    When answer is given:
        {"report": str, "next_q": str|None, "next_idx": int,
         "is_followup": bool, "stage_completed": bool,
         "all_completed": bool, "score_json": dict}
    """
    orch = _get_orchestrator(api_key)

    if resume:
        orch.analyze_resume(resume)
    if not orch._context:
        orch.fetch_context(topic)

    return orch.step(user, topic, idx, question, answer, history, resume, custom_questions)
