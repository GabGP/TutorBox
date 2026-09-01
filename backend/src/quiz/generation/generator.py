"""Pipeline for LLM question generation, schema enforcement, SymPy and deduplication validation."""

import json
import random

from quiz.contracts.models import QuizQuestion
from quiz.generation.llm_client import LLMClient
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
from quiz.validation.deduplication import DeduplicationValidator
from quiz.validation.taxonomy_validator import TaxonomyValidator
from quiz.validation.validator import MathValidatorInterface, SymPyMathValidator


class GenerationError(Exception):
    """Raised when the question generation and retry pipeline fails."""


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

    def generate(
        self,
        topic: str,
        subconcept: str | None = None,
        max_retries: int = 3,
        question_id: str | None = None,
    ) -> QuizQuestion:
        """Generates a validated diagnostic quiz question using a feedback-driven retry loop.

        Args:
            topic: The mathematics curriculum domain (e.g., 'pre_algebra', 'arithmetic').
            subconcept: The specific subtopic (e.g., 'two_step_equations').
            max_retries: Maximum number of generation attempts with feedback injection.
            question_id: Optional explicit question ID.

        Returns:
            A fully validated, SymPy-verified, shuffled QuizQuestion.

        Raises:
            GenerationError: If the SLM fails or candidate cannot be validated within max_retries.
        """
        system_prompt = build_quiz_system_prompt()
        base_user_prompt = build_quiz_user_prompt(topic, subconcept)
        current_user_prompt = base_user_prompt
        accumulated_errors: list[str] = []

        for attempt in range(1, max_retries + 1):
            # 1. Request completion from local SLM
            try:
                raw_response = self.llm_client.generate(
                    system_prompt, current_user_prompt
                )
            except Exception as llm_err:
                raise GenerationError(
                    f"SLM completion request failed on attempt {attempt}: {llm_err}"
                ) from llm_err

            # 2. Extract and parse JSON structure from model output
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

            # 3. Execute 4-stage validation (Schema -> Taxonomy -> SymPy Math -> Deduplication)
            validated_question, stage_errors = process_generated_response(
                parsed_json=parsed_json,
                topic=topic,
                subconcept=subconcept,
                question_id=question_id,
                math_validator=self.validator,
                taxonomy_validator=self.taxonomy_validator,
                dedup_validator=self.dedup_validator,
            )

            # 4. Handle validation failures by injecting error feedback for regeneration
            if stage_errors:
                accumulated_errors.extend(stage_errors)
                current_user_prompt = build_feedback_prompt(
                    base_user_prompt, accumulated_errors
                )
                continue

            # 5. Permute option keys and distractor order to prevent student guessing patterns
            if validated_question is not None:
                return shuffle_quiz_question(validated_question, rng=self.rng)

        raise GenerationError(
            f"Failed to generate a valid quiz question after {max_retries} attempts. "
            f"Errors: {'; '.join(accumulated_errors)}"
        )
