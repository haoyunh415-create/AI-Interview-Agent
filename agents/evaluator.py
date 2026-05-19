from agents.base import BaseAgent
from core.logging_config import get_logger

_log = get_logger("agent.evaluator")

EVALUATOR_ROLE = """你是一位严格的面试评价官（Evaluator Agent）。
你的职责是对候选人的回答进行多维度打分和点评。

评分维度（每项0-10分）：
- correctness：技术准确性，概念是否正确
- logic：逻辑清晰度，推理过程是否严密
- depth：理解深度，是否触及本质原理
- expression：表达能力，是否简洁准确

追问判断标准（needs_followup）：
- 回答过于简短（少于30字）→ 需要追问
- 核心概念解释模糊或错误 → 需要追问
- 缺乏具体细节或实例 → 需要追问
- 回答了但未触及问题本质 → 需要追问
- 回答准确、深入、有细节 → 不需要追问

要求：
1. 公平客观，不受问题难度以外的因素影响
2. 结合面试阶段调整评分侧重
3. 给出具体、可操作的改进建议
4. 必须严格输出JSON格式"""

STAGE_EMPHASIS = {
    "基础": "重点评估对概念的理解准确性",
    "原理": "重点评估对底层机制的解释能力",
    "进阶": "重点评估解决复杂问题的思路",
    "项目": "重点评估实践经验和工程能力",
    "挑战": "重点评估创新思维和深度洞察",
}

MAX_FOLLOWUPS_PER_STAGE = 3


class Evaluator(BaseAgent):
    """Evaluates candidate answers with multi-dimensional scoring."""

    def __init__(self, api_key=None):
        super().__init__(
            name="evaluator",
            role=EVALUATOR_ROLE,
            temperature=0.0,
            api_key=api_key,
        )

    def evaluate(self, question, answer, stage, followup_count=0):
        """Score an answer and return structured feedback including followup decision."""
        emphasis = STAGE_EMPHASIS.get(stage, "")

        followup_instruction = ""
        if followup_count >= MAX_FOLLOWUPS_PER_STAGE:
            followup_instruction = "\n注意：本阶段追问次数已达上限，请设置 needs_followup 为 false。"

        prompt = (
            "请对候选人的面试表现进行打分评估。\n"
            f"问题：{question}\n"
            f"回答：{answer}\n"
            f"阶段：{stage}\n"
            f"评估重点：{emphasis}\n"
            f"{followup_instruction}\n"
            "严格按以下 JSON 格式输出，不要输出其他内容：\n"
            '{"correctness": 0, "logic": 0, "depth": 0, "expression": 0, '
            '"summary": "简短评价", "improvement": "改进建议", '
            '"needs_followup": false, "followup_reason": ""}\n'
            "各维度 0-10 分。needs_followup 为 true 时需填写 followup_reason。\n"
        )
        result = self.invoke_json(prompt)

        if followup_count >= MAX_FOLLOWUPS_PER_STAGE:
            result["needs_followup"] = False

        _log.info("scores: correctness=%s logic=%s depth=%s expression=%s",
                  result.get("correctness"), result.get("logic"),
                  result.get("depth"), result.get("expression"))
        return result

    def should_followup(self, score_json):
        """Decide whether a follow-up is needed based on scores."""
        if not isinstance(score_json, dict):
            return False
        if score_json.get("needs_followup") is True:
            return True
        if score_json.get("needs_followup") is False:
            return False
        depth = score_json.get("depth", 10)
        correctness = score_json.get("correctness", 10)
        return depth < 5 or correctness < 5

    def format_report(self, score_json):
        """Format score JSON into human-readable report string."""
        if isinstance(score_json, dict):
            s = score_json
            lines = [
                f"正确性: {s.get('correctness', '?')} | "
                f"逻辑: {s.get('logic', '?')} | "
                f"深度: {s.get('depth', '?')} | "
                f"表达: {s.get('expression', '?')}",
                "",
                f"点评: {s.get('summary', '无')}",
                "",
                f"改进建议: {s.get('improvement', '继续深化学习')}",
            ]
            if s.get("needs_followup"):
                lines.extend(["", f"追问原因: {s.get('followup_reason', '需要进一步考察')}"])
            return "\n".join(lines)
        return str(score_json)
