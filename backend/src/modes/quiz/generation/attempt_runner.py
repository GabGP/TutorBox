"""Single-attempt execution, LLM query dispatch, and error recording for quiz generation."""

import json
from typing import Any

from core.llm import LLMClient
from modes.quiz.contracts.models import QuizQuestion
from modes.quiz.generation.generation_state import GenerationState
from modes.quiz.generation.prompt import build_feedback_prompt
from modes.quiz.generation.response_processor import (
    extract_json_dict,
    extract_scratchpad,
    process_generated_response,
)
from modes.quiz.validation.deduplication import DeduplicationValidator
from modes.quiz.validation.distractor_consistency import DistractorConsistencyValidator
from modes.quiz.validation.taxonomy_validator import TaxonomyValidator
from modes.quiz.validation.validator import MathValidatorInterface


def execute_llm_query(
    client: LLMClient,
    system_prompt: str,
    user_prompt: str,
    response_format: dict[str, Any],
) -> str:
    """Executes the LLM request handling optional structured response format."""
    try:
        return client.generate(system_prompt, user_prompt, response_format)
    except TypeError:
        return client.generate(system_prompt, user_prompt)


def execute_generation_attempt(
    client: LLMClient,
    system_prompt: str,
    base_user_prompt: str,
    response_format: dict[str, Any],
    state: GenerationState,
    topic: str,
    subconcept: str | None,
    question_id: str | None,
    math_validator: MathValidatorInterface,
    taxonomy_validator: TaxonomyValidator,
    dedup_validator: DeduplicationValidator,
    distractor_validator: DistractorConsistencyValidator | None = None,
) -> QuizQuestion | None:
    """Executes a single generation attempt and updates state on rejection or error.

    Returns the validated QuizQuestion on success, or None when the candidate
    fails JSON parsing or multi-stage validation.
    """
    # 1. Query local SLM completion endpoint with structured format
    try:
        raw_response = execute_llm_query(
            client, system_prompt, state.current_user_prompt, response_format
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
        return None

    # 3. Extract and record derivation scratchpad for telemetry
    state.record_scratchpad(extract_scratchpad(parsed_json))

    # 4. Execute 5-stage validation (Schema, Taxonomy, SymPy Math, Distractor, Deduplication)
    validated_question, stage_errors = process_generated_response(
        parsed_json=parsed_json,
        topic=topic,
        subconcept=subconcept,
        question_id=question_id,
        math_validator=math_validator,
        taxonomy_validator=taxonomy_validator,
        dedup_validator=dedup_validator,
        distractor_validator=distractor_validator,
    )

    # 5. If validation failed, accumulate feedback and record rejection
    if stage_errors:
        next_prompt = build_feedback_prompt(
            base_user_prompt, state.accumulated_errors + stage_errors
        )
        state.record_rejection(stage_errors, next_prompt)
        return None

    # 6. Validation succeeded: return validated question candidate
    return validated_question
