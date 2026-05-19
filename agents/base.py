import json
import re
import os
import time
from core.llm import get_llm
from core.logging_config import get_logger, log_duration


class BaseAgent:
    def __init__(self, name, role, temperature=None, api_key=None):
        self.name = name
        self.role = role
        self._temperature = temperature
        self._api_key = api_key if api_key else os.getenv("DEEPSEEK_API_KEY")
        self._logger = get_logger(f"agent.{name}")

    def invoke(self, prompt, temperature=None):
        full_prompt = f"{self.role}\n\n{prompt}"
        temp = temperature if temperature is not None else self._temperature
        self._logger.info("invoke (temp=%.1f, prompt_len=%d)", temp, len(full_prompt))
        t0 = time.monotonic()
        result = get_llm(self._api_key, temp).invoke(full_prompt).content
        log_duration(self._logger, f"invoke [{self.name}]", t0)
        return result

    def invoke_stream(self, prompt, temperature=None):
        """Yield tokens one at a time for Streamlit write_stream."""
        full_prompt = f"{self.role}\n\n{prompt}"
        temp = temperature if temperature is not None else self._temperature
        self._logger.info("invoke_stream (temp=%.1f, prompt_len=%d)", temp, len(full_prompt))
        t0 = time.monotonic()
        chunk_count = 0
        for chunk in get_llm(self._api_key, temp).stream(full_prompt):
            if chunk.content:
                chunk_count += 1
                yield chunk.content
        log_duration(self._logger, f"invoke_stream [{self.name}] ({chunk_count} chunks)", t0)

    def invoke_json(self, prompt, temperature=None):
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

        self._logger.warning("JSON parse failed, returning raw response")
        return {"raw": raw}

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name!r}>"
