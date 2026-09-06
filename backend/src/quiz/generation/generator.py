"""Pipeline for LLM question generation, schema enforcement, SymPy and distractor verification."""

import random

from core.llm import LLMClient
from quiz.generation.attempt_runner import execute_generation_attempt
from quiz.generation.generation_state import GenerationState
from quiz.generation.prompt import (
    build_quiz_system_prompt,
    build_quiz_user_prompt,
)
from quiz.generation.response_format import build_quiz_response_format
from quiz.generation.shuffler import shuffle_quiz_question
from quiz.generation.types import (
    GenerationError,
    GenerationResult,
    get_quiz_max_retries,
)
from quiz.validation.deduplication import DeduplicationValidator
from quiz.validation.distractor_consistency import DistractorConsistencyValidator
from quiz.validation.taxonomy_validator import TaxonomyValidator
from quiz.validation.validator import MathValidatorInterface, SymPyMathValidator

__all__ = ["GenerationError", "GenerationResult", "QuizQuestionGenerator"]


class QuizQuestionGenerator:
    """Orchestrates LLM generation, schema validation, SymPy math and distractor verification."""

    def __init__(
        self,
        llm_client: LLMClient,
        validator: MathValidatorInterface | None = None,
        taxonomy_validator: TaxonomyValidator | None = None,
        deduplication_validator: DeduplicationValidator | None = None,
        distractor_validator: DistractorConsistencyValidator | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.validator = validator or SymPyMathValidator()
        self.taxonomy_validator = taxonomy_validator or TaxonomyValidator()
        self.dedup_validator = deduplication_validator or DeduplicationValidator()
        self.distractor_validator = (
            distractor_validator or DistractorConsistencyValidator()
        )
        self.rng = rng

    def _resolve_model_name(self) -> str:
        """Extracts the model identifier from the underlying LLM client."""
        client = self.llm_client
        return (
            getattr(client, "model", None)
            or getattr(client, "model_name", None)
            or "unknown"
        )

    def generate(
        self,
        topic: str,
        subconcept: str | None = None,
        max_retries: int | None = None,
        question_id: str | None = None,
    ) -> GenerationResult:
        """Generates a validated diagnostic quiz question using a feedback-driven retry loop."""
        # 1. Prepare subconcept-aware system prompt, base user prompt, and JSON schema format
        retries = max_retries if max_retries is not None else get_quiz_max_retries()
        system_prompt = build_quiz_system_prompt(topic, subconcept)
        base_user_prompt = build_quiz_user_prompt(topic, subconcept)
        response_format = build_quiz_response_format()

        # 2. Initialize mutable generation state for retry and telemetry tracking
        state = GenerationState(
            model_name=self._resolve_model_name(),
            base_user_prompt=base_user_prompt,
            current_user_prompt=base_user_prompt,
            max_retries=retries,
        )

        # 3. Execute feedback-driven retry loop up to max_retries attempts
        while state.attempt <= state.max_retries:
            validated_question = execute_generation_attempt(
                client=self.llm_client,
                system_prompt=system_prompt,
                base_user_prompt=base_user_prompt,
                response_format=response_format,
                state=state,
                topic=topic,
                subconcept=subconcept,
                question_id=question_id,
                math_validator=self.validator,
                taxonomy_validator=self.taxonomy_validator,
                dedup_validator=self.dedup_validator,
                distractor_validator=self.distractor_validator,
            )

            # 4. Success: shuffle options to eliminate positional bias and package result
            if validated_question is not None:
                shuffled = shuffle_quiz_question(validated_question, rng=self.rng)
                return GenerationResult(
                    question=shuffled, metadata=state.build_metadata()
                )

        # 5. Pipeline exhausted max retries without producing a valid question
        raise state.build_exhaustion_error()
