"""Bounded access to the tutor model on the local completion server.

The Jetson answers a few requests at a time; beyond `max_concurrent` a turn
waits up to `queue_seconds` and then gives up, so the child gets the
deterministic hint instead of an endless spinner. Any server error is also a
None: the tutor never depends on the model to answer.
"""

import logging
import threading
from typing import Any

from core.config.tutor_settings import TutorConfig
from core.llm import LLMClient, LocalSLMClient

__all__ = ["TutorGateway", "TutorSLMClient"]

logger = logging.getLogger(__name__)


class TutorSLMClient(LocalSLMClient):
    """OpenAI-compatible client for the tutor model, with a token cap.

    DeepSeek recommends no system prompt for its R1 distills, so an empty system
    prompt sends a single user turn.
    """

    def __init__(self, config: TutorConfig) -> None:
        super().__init__(
            model=config.model_name,
            temperature=config.temperature,
            timeout_seconds=config.timeout_seconds,
        )
        self.max_tokens = config.max_tokens

    def _build_request_payload(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        return payload


class TutorGateway:
    """Runs at most `max_concurrent` completions; None when busy or failing."""

    def __init__(
        self, client: LLMClient, max_concurrent: int, queue_seconds: float
    ) -> None:
        self._client = client
        self._slots = threading.BoundedSemaphore(max_concurrent)
        self._queue_seconds = queue_seconds

    def complete(self, prompt: str) -> str | None:
        if not self._slots.acquire(timeout=self._queue_seconds):
            logger.warning("Tutor model busy; answering with a deterministic hint.")
            return None
        try:
            return self._client.generate("", prompt)
        except (RuntimeError, TypeError, ValueError, OSError) as err:
            logger.warning("Tutor model unavailable: %s", err)
            return None
        finally:
            self._slots.release()
