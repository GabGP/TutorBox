"""State management for iterative SLM quiz question generation and rejection tracking."""

import time
from dataclasses import dataclass, field

from quiz.contracts.models import GenerationMetadata
from quiz.generation.types import GenerationError


@dataclass
class GenerationState:
    """Encapsulates mutable lifecycle state for a quiz generation execution."""

    model_name: str
    base_user_prompt: str
    current_user_prompt: str
    max_retries: int
    start_time: float = field(default_factory=time.perf_counter)
    attempt: int = 1
    accumulated_errors: list[str] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        """Returns elapsed wall-clock milliseconds rounded to 2 decimal places."""
        return round((time.perf_counter() - self.start_time) * 1000.0, 2)

    def record_rejection(self, errors: list[str], next_prompt: str) -> None:
        """Appends new rejection errors, updates the prompt, and advances attempt."""
        self.accumulated_errors.extend(errors)
        self.current_user_prompt = next_prompt
        self.attempt += 1

    def build_metadata(self) -> GenerationMetadata:
        """Constructs telemetry metadata upon successful question generation."""
        return GenerationMetadata(
            model_name=self.model_name,
            attempts=self.attempt,
            duration_ms=self.duration_ms,
            rejection_history=list(self.accumulated_errors),
        )

    def build_exhaustion_error(self) -> GenerationError:
        """Constructs a descriptive GenerationError when retries are exhausted."""
        error_summary = (
            "; ".join(self.accumulated_errors)
            if self.accumulated_errors
            else "No specific validation errors recorded"
        )
        return GenerationError(
            f"Failed to generate a valid quiz question after {self.max_retries} attempts. "
            f"Errors: {error_summary}",
            attempts=self.max_retries,
            duration_ms=self.duration_ms,
            model_name=self.model_name,
            accumulated_errors=list(self.accumulated_errors),
        )

    def build_llm_failure_error(self, cause: Exception) -> GenerationError:
        """Constructs a descriptive GenerationError when an LLM transport call fails."""
        return GenerationError(
            f"SLM completion request failed on attempt {self.attempt}: {cause}",
            attempts=self.attempt,
            duration_ms=self.duration_ms,
            model_name=self.model_name,
            accumulated_errors=list(self.accumulated_errors),
        )
