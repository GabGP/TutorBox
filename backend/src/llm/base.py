"""Abstract LLM client interface for local and remote language model completions."""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract interface for LLM completions."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generates completion text given system and user prompts."""
