from agents.base import BaseAgent

REPORT_WRITER_ROLE = """你是一位面试报告撰写官（Report Writer Agent）。
你的职责是综合面试全过程的问答记录和评分，生成一份结构化、有洞察力的面试总结。

要求：
1. 客观公正，既肯定优点也指出不足
2. 结合候选人的简历背景做个性化分析
3. 给出具体可执行的学习建议
4. 用中文输出，条理清晰，分段明确"""


class ReportWriter(BaseAgent):
    """Generates interview summary reports."""

    def __init__(self, api_key=None):
        super().__init__(
            name="report_writer",
            role=REPORT_WRITER_ROLE,
            temperature=0.5,
            api_key=api_key,
        )

    def _build_summary_prompt(self, questions, answers, scores, profile=None):
        if not questions:
            return None

        profile_context = ""
        if profile and profile.get("tech_stack"):
            profile_context = (
                f"\n候选人背景：\n"
                f"- 级别：{profile.get('level', '未知')}\n"
                f"- 技术栈：{', '.join(profile.get('tech_stack', []))}\n"
                f"- 专长：{', '.join(profile.get('domains', []))}\n"
                f"- 项目亮点：{', '.join(profile.get('highlights', []))}\n"
            )

        return (
            "请总结这场面试的整体表现：\n\n"
            f"问题列表：{questions}\n"
            f"回答列表：{answers}\n"
            f"评分记录：{scores}\n"
            f"{profile_context}\n"
            "输出一个完整的面试总结报告，包括：\n"
            "1. 整体表现评价（优秀/良好/一般/需加强）\n"
            "2. 各维度分析（正确性、逻辑、深度、表达）\n"
            "3. 主要优点（至少2条）\n"
            "4. 需要加强的地方（至少2条，结合简历背景）\n"
            "5. 针对性学习建议（具体到技术或课程方向）\n"
            "6. 下一步面试准备建议\n\n"
            "用中文输出，条理清晰，使用适当的标题和分段。\n"
        )

    def generate_summary(self, questions, answers, scores, profile=None):
        prompt = self._build_summary_prompt(questions, answers, scores, profile)
        if prompt is None:
            return "暂无面试记录"
        return self.invoke(prompt)

    def generate_summary_stream(self, questions, answers, scores, profile=None):
        prompt = self._build_summary_prompt(questions, answers, scores, profile)
        if prompt is None:
            yield "暂无面试记录"
            return
        yield from self.invoke_stream(prompt)

    def generate_final_report(self, history, profile=None):
        """Generate a final report from interview history records."""
        questions = [h.get("q", "") for h in history]
        answers = [h.get("a", "") for h in history]
        scores = [h.get("score", "无") for h in history]
        return self.generate_summary(questions, answers, scores, profile)
