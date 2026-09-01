"""Pipeline for LLM question generation, schema enforcement, and SymPy validation."""

import json
import random
import re
import uuid
from typing import Any

from pydantic import ValidationError

from quiz.contracts.models import QuizQuestion
from quiz.contracts.schema import validate_quiz_question_dict
from quiz.generation.llm_client import LLMClient
from quiz.generation.prompt import (
    build_feedback_prompt,
    build_quiz_system_prompt,
    build_quiz_user_prompt,
)
from quiz.generation.shuffler import shuffle_quiz_question
from quiz.validation.taxonomy_validator import TaxonomyValidator
from quiz.validation.validator import MathValidatorInterface, SymPyMathValidator


class GenerationError(Exception):
    """Raised when the question generation and retry pipeline fails."""


class QuizQuestionGenerator:
    """Orchestrates LLM generation, schema validation, and SymPy math verification."""

    def __init__(
        self,
        llm_client: LLMClient,
        validator: MathValidatorInterface | None = None,
        taxonomy_validator: TaxonomyValidator | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.validator = validator or SymPyMathValidator()
        self.taxonomy_validator = taxonomy_validator or TaxonomyValidator()
        self.rng = rng

    def _extract_json_dict(self, raw_output: str) -> dict[str, Any]:
        """Extracts outermost JSON dictionary from Markdown code fences or curly braces."""
        cleaned = raw_output.strip()
        fenced_pattern = r"```(?:json)?\s*(\{.*\})\s*```"
        if match := (
            re.search(fenced_pattern, cleaned, re.DOTALL)
            or re.search(r"(\{.*\})", cleaned, re.DOTALL)
        ):
            cleaned = match.group(1).strip()
        return json.loads(cleaned)

    @staticmethod
    def _resolve_question_id(
        parsed_json: dict[str, Any], question_id: str | None
    ) -> str:
        """Assigns the explicit ID or generates a unique fallback ID."""
        if question_id:
            return question_id
        existing = parsed_json.get("id")
        if existing and existing != "gen_sample_01":
            return str(existing)
        return f"q_gen_{uuid.uuid4().hex[:12]}"

    def _validate_candidate(
        self,
        parsed_json: dict[str, Any],
        topic: str,
        subconcept: str | None,
        question_id: str | None,
    ) -> tuple[QuizQuestion | None, list[str]]:
        """Performs 3-stage validation: Pydantic Schema, Taxonomy, and SymPy math checks."""
        parsed_json["id"] = self._resolve_question_id(parsed_json, question_id)
        # Stage 1: Pydantic Schema Validation
        try:
            candidate = validate_quiz_question_dict(parsed_json)
        except (ValidationError, ValueError, TypeError) as schema_error:
            return None, [f"Schema violation: {schema_error}"]

        # Stage 2: Pedagogical Taxonomy Validation
        taxonomy_result = self.taxonomy_validator.validate_question_taxonomy(
            candidate, expected_topic=topic, expected_subconcept=subconcept
        )
        if not taxonomy_result.is_valid:
            return None, taxonomy_result.errors

        # Stage 3: Deterministic SymPy Mathematical Truth Verification
        math_result = self.validator.validate_question_math(candidate)
        return (candidate, []) if math_result.is_valid else (None, math_result.errors)

    def generate(
        self,
        topic: str,
        subconcept: str | None = None,
        max_retries: int = 3,
        question_id: str | None = None,
    ) -> QuizQuestion:
        """Generates a validated diagnostic quiz question using a feedback-driven retry loop."""
        system_prompt = build_quiz_system_prompt()
        base_user_prompt = build_quiz_user_prompt(topic, subconcept)
        current_user_prompt = base_user_prompt
        accumulated_errors: list[str] = []

        for _ in range(max_retries):
            try:
                raw_response = self.llm_client.generate(
                    system_prompt, current_user_prompt
                )
            except Exception as llm_err:
                raise GenerationError(
                    f"SLM completion request failed: {llm_err}"
                ) from llm_err

            # Attempt JSON extraction
            try:
                parsed_json = self._extract_json_dict(raw_response)
                if not isinstance(parsed_json, dict):
                    raise TypeError("Extracted JSON root is not an object")
            except (json.JSONDecodeError, TypeError, ValueError) as json_error:
                accumulated_errors.append(f"Invalid JSON output: {json_error}")
                current_user_prompt = build_feedback_prompt(
                    base_user_prompt, accumulated_errors
                )
                continue

            # Run 3-stage validation pipeline
            validated_question, stage_errors = self._validate_candidate(
                parsed_json, topic, subconcept, question_id
            )
            if stage_errors:
                accumulated_errors.extend(stage_errors)
                current_user_prompt = build_feedback_prompt(
                    base_user_prompt, accumulated_errors
                )
                continue

            if validated_question is not None:
                # Randomize option ordering to prevent position bias
                return shuffle_quiz_question(validated_question, rng=self.rng)

        raise GenerationError(
            f"Failed to generate a valid quiz question after {max_retries} attempts. "
            f"Errors: {'; '.join(accumulated_errors)}"
        )
