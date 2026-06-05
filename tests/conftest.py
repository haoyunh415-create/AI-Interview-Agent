"""Test fixtures — mock heavy dependencies to avoid torch/transformers crash."""

import os

# Disable rate limiting for all tests (set before backend module imports)
os.environ["DISABLE_RATE_LIMIT"] = "1"

import sys
from unittest.mock import MagicMock

# Prevent langchain_openai → transformers → torch import chain
# which crashes on this Windows/PyTorch config
_mock_langchain_openai = MagicMock()
_mock_langchain_openai.ChatOpenAI = MagicMock()
sys.modules["langchain_openai"] = _mock_langchain_openai
sys.modules["langchain_openai.chat_models"] = MagicMock()
sys.modules["langchain_openai.chat_models.azure"] = MagicMock()
sys.modules["langchain_openai.chat_models.base"] = MagicMock()

_mock_langchain_community = MagicMock()
sys.modules["langchain_community"] = _mock_langchain_community
sys.modules["langchain_community.vectorstores"] = MagicMock()
sys.modules["langchain_community.document_loaders"] = MagicMock()


# Prevent torch/transformers from loading at all
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["chromadb"] = MagicMock()
sys.modules["reportlab"] = MagicMock()
sys.modules["reportlab.platypus"] = MagicMock()
sys.modules["reportlab.lib.styles"] = MagicMock()
sys.modules["reportlab.lib.pagesizes"] = MagicMock()
sys.modules["reportlab.pdfbase"] = MagicMock()
sys.modules["reportlab.pdfbase.ttfonts"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
