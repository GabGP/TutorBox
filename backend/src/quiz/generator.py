import json
import re
import uuid
from typing import Any

from pydantic import ValidationError

from quiz.llm_client import LLMClient
from quiz.models import QuizQuestion
from quiz.prompt import (
    build_feedback_prompt,
    build_quiz_system_prompt,
    build_quiz_user_prompt,
)
from quiz.schema import validate_quiz_question_dict
from quiz.validator import MathValidatorInterface, SymPyMathValidator


class GenerationError(Exception):
    """Raised when the question generation and retry pipeline fails."""


class QuizQuestionGenerator:
    """Orchestrates LLM generation, schema validation, and SymPy math verification."""

    def __init__(
        self,
        llm_client: LLMClient,
        validator: MathValidatorInterface | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.validator = validator or SymPyMathValidator()

    def _extract_json_dict(self, raw_output: str) -> dict[str, Any]:
        """Extracts the outermost JSON dictionary from raw LLM output."""
        cleaned_output = raw_output.strip()
        if code_fence_match := re.search(
            r"```(?:json)?\s*(\{.*\})\s*```", cleaned_output, re.DOTALL
        ):
            cleaned_output = code_fence_match.group(1).strip()
        elif json_bracket_match := re.search(r"(\{.*\})", cleaned_output, re.DOTALL):
            cleaned_output = json_bracket_match.group(1).strip()
        return json.loads(cleaned_output)

    def generate(
        self,
        topic: str,
        subconcept: str | None = None,
        max_retries: int = 3,
        question_id: str | None = None,
    ) -> QuizQuestion:
        system_prompt = build_quiz_system_prompt()
        base_user_prompt = build_quiz_user_prompt(topic, subconcept)
        current_user_prompt = base_user_prompt
        accumulated_errors: list[str] = []

        for _ in range(max_retries):
            raw_response = self.llm_client.generate(system_prompt, current_user_prompt)
            step_errors: list[str] = []

            try:
                parsed_json = self._extract_json_dict(raw_response)
                if not isinstance(parsed_json, dict):
                    raise TypeError("Extracted JSON root is not an object")
            except (json.JSONDecodeError, TypeError, ValueError) as json_error:
                step_errors.append(f"Invalid JSON output: {json_error}")
                accumulated_errors.extend(step_errors)
                current_user_prompt = build_feedback_prompt(
                    base_user_prompt, accumulated_errors
                )
                continue

            if not parsed_json.get("id"):
                parsed_json["id"] = question_id or f"q_gen_{uuid.uuid4().hex[:8]}"

            try:
                question = validate_quiz_question_dict(parsed_json)
            except (ValidationError, ValueError, TypeError) as schema_error:
                step_errors.append(f"Schema violation: {schema_error}")
                accumulated_errors.extend(step_errors)
                current_user_prompt = build_feedback_prompt(
                    base_user_prompt, accumulated_errors
                )
                continue

            math_validation_result = self.validator.validate_question_math(question)
            if not math_validation_result.is_valid:
                step_errors.extend(math_validation_result.errors)
                accumulated_errors.extend(step_errors)
                current_user_prompt = build_feedback_prompt(
                    base_user_prompt, accumulated_errors
                )
                continue

            return question

        raise GenerationError(
            f"Failed to generate a valid quiz question after {max_retries} attempts. "
            f"Errors: {'; '.join(accumulated_errors)}"
        )
