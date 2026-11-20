"""Abstract LLM client interface for local and remote language model completions."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class LLMClient(ABC):
    """Abstract interface for LLM completions."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any] | None = None,
        should_stop: Callable[[], bool] | None = None,
    ) -> str:
        """Generates completion text given system and user prompts and optional response format.

        When `should_stop` turns True mid-request the client drops the request
        and raises LLMCallCancelled (see core.llm.cancellable_post).
        """
