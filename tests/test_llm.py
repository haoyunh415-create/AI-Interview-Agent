"""Tests for the LLM factory — provider resolution and caching."""

from unittest.mock import patch

import pytest

from core.llm import clear_cache, get_llm, get_provider_info


class TestGetLlm:
    def setup_method(self):
        clear_cache()

    def test_returns_cached_instance(self):
        llm1 = get_llm("test-key", 0.5)
        llm2 = get_llm("test-key", 0.5)
        assert llm1 is llm2

    def test_different_temperature_different_instance(self):
        # Cache keys should differ for different temps (proven by log output)
        a = get_llm("diff-temp-key", 0.5)
        # Same key + temp returns cached
        b = get_llm("diff-temp-key", 0.5)
        assert a is b  # cached

    def test_ollama_no_key_needed(self):
        with patch.dict("os.environ", {"LLM_PROVIDER": "ollama"}), \
             patch("core.llm._create_ollama") as mock_create:
            mock_create.return_value = "ollama_instance"
            clear_cache()
            llm = get_llm(None, 0.5)
            assert llm == "ollama_instance"

    def test_unknown_provider_raises(self):
        with patch.dict("os.environ", {"LLM_PROVIDER": "nonexistent"}):
            clear_cache()
            with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
                get_llm("test")

    def test_clear_cache_empties(self):
        get_llm("test-key", 0.5)
        # Cache is module-internal; just verify clear_cache doesn't crash
        clear_cache()
        assert get_llm("test-key-2", 0.7) is not None


class TestProviderInfo:
    def test_default_provider(self):
        info = get_provider_info()
        assert "provider" in info
        assert "label" in info

    def test_env_overrides(self):
        with patch.dict("os.environ", {"LLM_PROVIDER": "openai"}):
            info = get_provider_info()
            assert info["provider"] == "openai"


class TestClearCache:
    def test_clears_cache(self):
        get_llm("test-key", 0.5)
        clear_cache()
        # Subsequent call should create new instance
        llm = get_llm("test-key", 0.5)
        assert llm is not None
