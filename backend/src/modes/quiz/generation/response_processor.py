"""Processing, JSON extraction, and multi-stage validation for SLM-generated quiz responses."""

import json
import re
import uuid
from typing import Any

from pydantic import ValidationError

from modes.quiz.contracts.models import QuizQuestion
from modes.quiz.contracts.sanitizer import sanitize_quiz_dict
from modes.quiz.contracts.schema import validate_quiz_question_dict
from modes.quiz.validation.deduplication import DeduplicationValidator
from modes.quiz.validation.distractor_consistency import DistractorConsistencyValidator
from modes.quiz.validation.taxonomy_validator import TaxonomyValidator
from modes.quiz.validation.validator import MathValidatorInterface


def extract_json_dict(raw_output: str) -> dict[str, Any]:
    """Extracts outermost JSON dictionary from Markdown code fences or raw curly braces."""
    cleaned = raw_output.strip()
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
    fenced_pat = r"```(?:json)?\s*(\{.*\})\s*```"
    match = re.search(fenced_pat, cleaned, re.DOTALL) or re.search(
        r"(\{.*\})", cleaned, re.DOTALL
    )
    if match:
        cleaned = match.group(1).strip()
    return json.loads(cleaned)


def resolve_question_id(parsed_json: dict[str, Any], question_id: str | None) -> str:
    """Assigns the explicit ID or generates a unique fallback ID."""
    if question_id:
        return question_id
    existing = parsed_json.get("id")
    if existing and existing != "gen_sample_01":
        return str(existing)
    return f"q_gen_{uuid.uuid4().hex[:12]}"


def extract_scratchpad(parsed_json: dict[str, Any]) -> str | None:
    """Extracts and removes ephemeral derivation scratchpad from candidate payload."""
    scratchpad = parsed_json.pop("derivation_scratchpad", None)
    if scratchpad is not None:
        cleaned = str(scratchpad).strip()
        return cleaned if cleaned else None
    return None


def process_generated_response(
    parsed_json: dict[str, Any],
    topic: str,
    subconcept: str | None,
    question_id: str | None,
    math_validator: MathValidatorInterface,
    taxonomy_validator: TaxonomyValidator,
    dedup_validator: DeduplicationValidator,
    distractor_validator: DistractorConsistencyValidator | None = None,
) -> tuple[QuizQuestion | None, list[str]]:
    """Executes the 5-stage deterministic validation pipeline on a parsed SLM JSON candidate.

    Stages:
        1. Schema Validation: Guarantees 1-correct + 3-distractor Pydantic contract compliance.
        2. Taxonomy Validation: Enforces topic, subconcept, and recognized misconception slugs.
        3. SymPy Math Validation: Proves mathematical truth and ensures distinct distractors.
        4. Distractor Consistency: Verifies numerical alignment between explanations and options.
        5. Deduplication Gate: Rejects candidate questions matching existing question bank items.
    """
    extract_scratchpad(parsed_json)
    parsed_json = sanitize_quiz_dict(parsed_json)
    parsed_json["id"] = resolve_question_id(parsed_json, question_id)

    # Stage 1: Pydantic schema structure validation
    try:
        candidate = validate_quiz_question_dict(parsed_json)
    except (ValidationError, ValueError, TypeError) as schema_error:
        return None, [f"Schema violation: {schema_error}"]

    # Stage 2: Pedagogical curriculum taxonomy & misconception whitelist
    taxonomy_result = taxonomy_validator.validate_question_taxonomy(
        candidate, expected_topic=topic, expected_subconcept=subconcept
    )
    if not taxonomy_result.is_valid:
        return None, taxonomy_result.errors

    # Stage 3: Deterministic SymPy mathematical truth & distractor collision check
    math_result = math_validator.validate_question_math(candidate)
    if not math_result.is_valid:
        return None, math_result.errors

    # Stage 4: Distractor explanation-to-option numerical consistency check
    active_distractor_validator = (
        distractor_validator or DistractorConsistencyValidator()
    )
    distractor_result = active_distractor_validator.validate_distractor_consistency(
        candidate
    )
    if not distractor_result.is_valid:
        return None, distractor_result.errors

    # Stage 5: Novelty verification against reference seed questions
    dedup_result = dedup_validator.validate_question_novelty(candidate)
    if not dedup_result.is_valid:
        return None, dedup_result.errors

    return candidate, []
