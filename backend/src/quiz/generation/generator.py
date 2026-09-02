"""Pipeline for LLM question generation, schema enforcement, SymPy and deduplication validation."""

import json
import random
import time

from llm import LLMClient
from quiz.contracts.models import GenerationMetadata
from quiz.generation.prompt import (
    build_feedback_prompt,
    build_quiz_system_prompt,
    build_quiz_user_prompt,
)
from quiz.generation.response_processor import (
    extract_json_dict,
    process_generated_response,
)
from quiz.generation.shuffler import shuffle_quiz_question
from quiz.generation.types import (
    GenerationError,
    GenerationResult,
    get_quiz_max_retries,
)
from quiz.validation.deduplication import DeduplicationValidator
from quiz.validation.taxonomy_validator import TaxonomyValidator
from quiz.validation.validator import MathValidatorInterface, SymPyMathValidator


class QuizQuestionGenerator:
    """Orchestrates LLM generation, schema validation, SymPy math and deduplication verification."""

    def __init__(
        self,
        llm_client: LLMClient,
        validator: MathValidatorInterface | None = None,
        taxonomy_validator: TaxonomyValidator | None = None,
        deduplication_validator: DeduplicationValidator | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.validator = validator or SymPyMathValidator()
        self.taxonomy_validator = taxonomy_validator or TaxonomyValidator()
        self.dedup_validator = deduplication_validator or DeduplicationValidator()
        self.rng = rng

    def _resolve_model_name(self) -> str:
        """Extracts the model identifier from the underlying LLM client."""
        return (
            getattr(self.llm_client, "model", None)
            or getattr(self.llm_client, "model_name", None)
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
        effective_max_retries = (
            max_retries if max_retries is not None else get_quiz_max_retries()
        )
        system_prompt = build_quiz_system_prompt()
        base_user_prompt = build_quiz_user_prompt(topic, subconcept)
        current_user_prompt = base_user_prompt
        accumulated_errors: list[str] = []
        model_name = self._resolve_model_name()
        start_time = time.perf_counter()

        for attempt in range(1, effective_max_retries + 1):
            # 1. Query local SLM completion endpoint
            try:
                raw_response = self.llm_client.generate(
                    system_prompt, current_user_prompt
                )
            except Exception as llm_err:
                duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                raise GenerationError(
                    f"SLM completion request failed on attempt {attempt}: {llm_err}",
                    attempts=attempt,
                    duration_ms=duration_ms,
                    model_name=model_name,
                    accumulated_errors=accumulated_errors,
                ) from llm_err

            # 2. Extract and parse root JSON object
            try:
                parsed_json = extract_json_dict(raw_response)
                if not isinstance(parsed_json, dict):
                    raise TypeError("Extracted JSON root is not an object")
            except (json.JSONDecodeError, TypeError, ValueError) as json_err:
                accumulated_errors.append(f"Invalid JSON output: {json_err}")
                current_user_prompt = build_feedback_prompt(
                    base_user_prompt, accumulated_errors
                )
                continue

            # 3. Execute 4-stage validation (Schema, Taxonomy, SymPy Math, Deduplication)
            validated_question, stage_errors = process_generated_response(
                parsed_json=parsed_json,
                topic=topic,
                subconcept=subconcept,
                question_id=question_id,
                math_validator=self.validator,
                taxonomy_validator=self.taxonomy_validator,
                dedup_validator=self.dedup_validator,
            )

            # 4. If validation failed, accumulate feedback and retry
            if stage_errors:
                accumulated_errors.extend(stage_errors)
                current_user_prompt = build_feedback_prompt(
                    base_user_prompt, accumulated_errors
                )
                continue

            # 5. Success: shuffle options to avoid positional bias and package result
            if validated_question is not None:
                duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                shuffled = shuffle_quiz_question(validated_question, rng=self.rng)
                metadata = GenerationMetadata(
                    model_name=model_name,
                    attempts=attempt,
                    duration_ms=duration_ms,
                    rejection_history=accumulated_errors,
                )
                return GenerationResult(question=shuffled, metadata=metadata)

        # 6. Pipeline exhausted max retries without producing a valid question
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        raise GenerationError(
            f"Failed to generate a valid quiz question after {effective_max_retries} attempts. "
            f"Errors: {'; '.join(accumulated_errors)}",
            attempts=effective_max_retries,
            duration_ms=duration_ms,
            model_name=model_name,
            accumulated_errors=accumulated_errors,
        )
