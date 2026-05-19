import json
import re
import os
from core.llm import get_llm


class BaseAgent:
    """Base class for all interview agents.

    Each agent has a distinct role (system prompt), temperature, and name.
    All share the same underlying LLM instance.
    """

    def __init__(self, name, role, temperature=None, api_key=None):
        self.name = name
        self.role = role
        self._temperature = temperature
        self._api_key = api_key if api_key else os.getenv("DEEPSEEK_API_KEY")

    def invoke(self, prompt, temperature=None):
        """Call LLM with role prefix and given prompt."""
        full_prompt = f"{self.role}\n\n{prompt}"
        temp = temperature if temperature is not None else self._temperature
        return get_llm(self._api_key, temp).invoke(full_prompt).content

    def invoke_json(self, prompt, temperature=None):
        """Call LLM and parse JSON response. Falls back gracefully."""
        raw = self.invoke(prompt, temperature)

        for pattern in [
            r"\{(?:[^{}]|\{[^{}]*\})*\}",
            r"\{.*?\}",
        ]:
            match = re.search(pattern, raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    continue

        # Fallback: extract JSON by tracking brace depth
        start = raw.find("{")
        if start != -1:
            depth = 0
            for i in range(start, len(raw)):
                if raw[i] == "{":
                    depth += 1
                elif raw[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(raw[start:i + 1])
                        except json.JSONDecodeError:
                            break

        return {"raw": raw}

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name!r}>"
