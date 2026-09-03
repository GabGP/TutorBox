"""Pipeline for LLM question generation, schema enforcement, SymPy and distractor verification."""

import json
import random
from typing import Any

from llm import LLMClient
from quiz.generation.generation_state import GenerationState
from quiz.generation.prompt import (
    build_feedback_prompt,
    build_quiz_response_format,
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
        return (
            getattr(self.llm_client, "model", None)
            or getattr(self.llm_client, "model_name", None)
            or "unknown"
        )

    def _execute_llm_query(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: dict[str, Any],
    ) -> str:
        """Executes the LLM request handling optional structured response format."""
        try:
            return self.llm_client.generate(system_prompt, user_prompt, response_format)
        except TypeError:
            return self.llm_client.generate(system_prompt, user_prompt)

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
        system_prompt = build_quiz_system_prompt(topic)
        base_user_prompt = build_quiz_user_prompt(topic, subconcept)
        response_format = build_quiz_response_format()

        state = GenerationState(
            model_name=self._resolve_model_name(),
            base_user_prompt=base_user_prompt,
            current_user_prompt=base_user_prompt,
            max_retries=effective_max_retries,
        )

        while state.attempt <= state.max_retries:
            # 1. Query local SLM completion endpoint with structured format
            try:
                raw_response = self._execute_llm_query(
                    system_prompt, state.current_user_prompt, response_format
                )
            except Exception as llm_err:
                raise state.build_llm_failure_error(llm_err) from llm_err

            # 2. Extract and parse root JSON object
            try:
                parsed_json = extract_json_dict(raw_response)
                if not isinstance(parsed_json, dict):
                    raise TypeError("Extracted JSON root is not an object")
            except (json.JSONDecodeError, TypeError, ValueError) as json_err:
                err_msg = f"Invalid JSON output: {json_err}"
                next_prompt = build_feedback_prompt(
                    base_user_prompt, state.accumulated_errors + [err_msg]
                )
                state.record_rejection([err_msg], next_prompt)
                continue

            # 3. Execute 5-stage validation (Schema, Taxonomy, SymPy Math, Distractor, Deduplication)
            validated_question, stage_errors = process_generated_response(
                parsed_json=parsed_json,
                topic=topic,
                subconcept=subconcept,
                question_id=question_id,
                math_validator=self.validator,
                taxonomy_validator=self.taxonomy_validator,
                dedup_validator=self.dedup_validator,
                distractor_validator=self.distractor_validator,
            )

            # 4. If validation failed, accumulate feedback and retry
            if stage_errors:
                next_prompt = build_feedback_prompt(
                    base_user_prompt, state.accumulated_errors + stage_errors
                )
                state.record_rejection(stage_errors, next_prompt)
                continue

            # 5. Success: shuffle options to avoid positional bias and package result
            if validated_question is not None:
                shuffled = shuffle_quiz_question(validated_question, rng=self.rng)
                return GenerationResult(
                    question=shuffled, metadata=state.build_metadata()
                )

        # 6. Pipeline exhausted max retries without producing a valid question
        raise state.build_exhaustion_error()
