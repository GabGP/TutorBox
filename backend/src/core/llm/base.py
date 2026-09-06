"""Abstract LLM client interface for local and remote language model completions."""

from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """Abstract interface for LLM completions."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Generates completion text given system and user prompts and optional response format."""
