from agents.base import BaseAgent

INTERVIEWER_ROLE = """你是一位资深的技术面试官（Interviewer Agent）。
你的职责是根据候选人的背景和当前面试阶段，提出精准、有深度的技术问题。

要求：
1. 每次只提一个问题
2. 问题要有层次感，能考察真实理解能力
3. 根据候选人级别调整难度
4. 避免重复之前问过的问题
5. 语气专业但不失亲和力"""


def get_level_bias(profile):
    """Return difficulty adjustment based on candidate level. Standalone function."""
    if not profile:
        return ""
    level = profile.get("level", "中级")
    biases = {
        "初级": "问题偏向基础概念，多给提示，鼓励为主",
        "中级": "基础与进阶结合，适当追问细节",
        "高级": "深入原理和架构设计，考察系统思维",
        "专家": "挑战前沿技术和创新方案，考察行业视野",
    }
    return biases.get(level, biases["中级"])


class Interviewer(BaseAgent):
    """Generates interview questions based on topic, stage, and candidate profile."""

    def __init__(self, api_key=None):
        super().__init__(
            name="interviewer",
            role=INTERVIEWER_ROLE,
            temperature=0.8,
            api_key=api_key,
        )

    def generate_question(
        self,
        topic,
        stage,
        context="",
        history=None,
        profile=None,
        custom_questions=None,
    ):
        """Generate a single interview question."""
        if custom_questions and history:
            idx = len(history)
            if idx < len(custom_questions):
                return custom_questions[idx]

        history_context = ""
        if history:
            history_context = "\n已问过的问题：\n" + "\n".join(
                "- " + h["q"] for h in history[-3:]
            )

        profile_context = ""
        level_bias = ""
        if profile and profile.get("tech_stack"):
            profile_context = (
                f"\n候选人背景：\n"
                f"- 级别：{profile.get('level', '未知')}\n"
                f"- 技术栈：{', '.join(profile.get('tech_stack', []))}\n"
                f"- 专长：{', '.join(profile.get('domains', []))}\n"
            )
            level_bias = get_level_bias(profile)

        prompt = (
            f"当前主题：{topic}\n"
            f"当前阶段：{stage}\n"
            f"参考知识：{context}\n"
            f"{history_context}\n"
            f"{profile_context}\n"
            f"难度建议：{level_bias}\n\n"
            "要求：\n"
            "1. 根据当前阶段和已问过的问题，提出【一个】新的技术面试题\n"
            "2. 禁止重复类似的问题\n"
            "3. 题目要具体且有深度，能考察真实理解能力\n"
            "4. 如果候选人有简历信息，针对其技术栈和项目出题\n"
            "5. 语气专业自然\n\n"
            "直接输出问题：\n"
        )
        return self.invoke(prompt)

    def generate_followup(self, original_question, answer, evaluation, stage):
        """Generate a follow-up question based on the previous answer's weakness."""
        followup_reason = evaluation.get("followup_reason", "回答不够深入")
        weakness_summary = evaluation.get("summary", "")

        prompt = (
            "你是一位技术面试官，需要对候选人的回答进行追问。\n\n"
            f"原问题：{original_question}\n"
            f"候选人回答：{answer}\n"
            f"评价：{weakness_summary}\n"
            f"追问原因：{followup_reason}\n"
            f"当前阶段：{stage}\n\n"
            "要求：\n"
            "1. 基于候选人的回答的不足之处，提出一个追问\n"
            "2. 追问不是新题目，而是引导候选人补充、深入或纠正之前的回答\n"
            "3. 追问要具体，指向回答中的薄弱点\n"
            "4. 语气为引导式，可以说'你刚才提到X，能否具体讲讲Y？'\n"
            "5. 不要重复原问题\n\n"
            "直接输出追问问题：\n"
        )
        return self.invoke(prompt, temperature=0.6)

    def generate_hint(self, question):
        """Generate a short hint for the given question."""
        prompt = (
            "基于这个问题，给考生一个简短的提示（10字以内），帮助他们理清答题方向。\n"
            f"问题：{question}\n"
            "只输出一个简洁的提示，不要多余内容：\n"
        )
        return self.invoke(prompt, temperature=0.3)
