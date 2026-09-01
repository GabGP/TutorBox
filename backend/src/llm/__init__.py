"""Shared LLM client package for local inference and simulation."""

from llm.base import LLMClient
from llm.client import (
    DEFAULT_SLM_BASE_URL,
    DEFAULT_SLM_MODEL_NAME,
    DEFAULT_SLM_TEMPERATURE,
    DEFAULT_SLM_TIMEOUT_SECONDS,
    LocalSLMClient,
)
from llm.mock import MockLLMClient

__all__ = [
    "DEFAULT_SLM_BASE_URL",
    "DEFAULT_SLM_MODEL_NAME",
    "DEFAULT_SLM_TEMPERATURE",
    "DEFAULT_SLM_TIMEOUT_SECONDS",
    "LLMClient",
    "LocalSLMClient",
    "MockLLMClient",
]
