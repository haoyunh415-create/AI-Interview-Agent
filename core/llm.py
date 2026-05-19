import os
from langchain_openai import ChatOpenAI
from core.config import LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE, LLM_TIMEOUT, LLM_MAX_RETRIES

_llms = {}


def get_llm(api_key=None, temperature=None):
    if api_key is None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
    if temperature is None:
        temperature = LLM_TEMPERATURE

    key = (api_key or "", temperature)
    if key not in _llms:
        _llms[key] = ChatOpenAI(
            model=LLM_MODEL,
            api_key=api_key,
            base_url=LLM_BASE_URL,
            temperature=temperature,
            request_timeout=LLM_TIMEOUT,
            max_retries=LLM_MAX_RETRIES,
        )
    return _llms[key]
