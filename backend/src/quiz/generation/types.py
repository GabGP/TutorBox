"""Data structures and custom exceptions for the quiz generation pipeline."""

from collections.abc import Iterator
from typing import Any

from config import DEFAULT_QUIZ_MAX_RETRIES, get_settings
from quiz.contracts.models import GenerationMetadata, QuizQuestion

DEFAULT_MAX_RETRIES: int = DEFAULT_QUIZ_MAX_RETRIES


def get_quiz_max_retries() -> int:
    """Returns configured max generation retries from settings."""
    return get_settings(reload=True).quiz.max_retries


class GenerationResult:
    """Encapsulates a generated quiz question and its execution telemetry metadata."""

    def __init__(self, question: QuizQuestion, metadata: GenerationMetadata) -> None:
        self.question = question
        self.metadata = metadata

    def __iter__(self) -> Iterator[Any]:
        return iter((self.question, self.metadata))

    def __getitem__(self, index: int) -> Any:
        return (self.question, self.metadata)[index]

    def __getattr__(self, name: str) -> Any:
        return getattr(self.question, name)


class GenerationError(Exception):
    """Raised when the question generation and retry pipeline fails."""

    def __init__(
        self,
        message: str,
        *,
        attempts: int = 1,
        duration_ms: float = 0.0,
        model_name: str = "unknown",
        accumulated_errors: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.duration_ms = duration_ms
        self.model_name = model_name
        self.accumulated_errors = accumulated_errors or []
