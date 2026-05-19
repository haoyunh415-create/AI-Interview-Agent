from agents.base import BaseAgent

RESUME_ANALYST_ROLE = """你是一位资深的简历分析师（Resume Analyst Agent）。
你的职责是深度分析候选人的简历，提取结构化信息，供面试官和评价官使用。

分析要点：
1. 技术栈：编程语言、框架、工具、云平台
2. 经验级别：初级/中级/高级/专家，依据工作年限和项目复杂度
3. 专长领域：NLP、CV、推荐系统、MLOps、数据工程等
4. 知识盲区：简历中未提及但行业内通常需要的能力
5. 项目亮点：最有价值的项目经验

输出严格的JSON格式，不要输出其他内容。"""


class ResumeAnalyst(BaseAgent):
    """Analyzes candidate resume and produces structured profile."""

    def __init__(self, api_key=None):
        super().__init__(
            name="resume_analyst",
            role=RESUME_ANALYST_ROLE,
            temperature=0.3,
            api_key=api_key,
        )

    def analyze(self, resume_text):
        """Analyze resume and return structured profile."""
        if not resume_text or not resume_text.strip():
            return {
                "tech_stack": [],
                "level": "未知",
                "domains": [],
                "gaps": [],
                "highlights": [],
                "years_of_experience": 0,
            }

        prompt = f"""请分析以下简历，提取结构化信息。

简历内容：
{resume_text[:2000]}

请严格按以下JSON格式输出：
{{
    "tech_stack": ["技术1", "技术2", ...],
    "level": "初级/中级/高级/专家",
    "domains": ["领域1", "领域2", ...],
    "gaps": ["知识盲区1", "知识盲区2", ...],
    "highlights": ["项目亮点1", "项目亮点2", ...],
    "years_of_experience": 数字
}}
"""
        return self.invoke_json(prompt)

    def get_level_bias(self, profile):
        """Return difficulty adjustment based on candidate level."""
        level = profile.get("level", "中级")
        biases = {
            "初级": "问题偏向基础概念，多给提示，鼓励为主",
            "中级": "基础与进阶结合，适当追问细节",
            "高级": "深入原理和架构设计，考察系统思维",
            "专家": "挑战前沿技术和创新方案，考察行业视野",
        }
        return biases.get(level, biases["中级"])
