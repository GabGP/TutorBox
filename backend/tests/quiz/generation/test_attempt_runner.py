"""Unit tests for attempt_runner module."""

import json
from typing import Any

import pytest

from core.llm import LLMClient, MockLLMClient
from quiz.generation.attempt_runner import (
    execute_generation_attempt,
    execute_llm_query,
)
from quiz.generation.generation_state import GenerationState
from quiz.generation.response_format import build_quiz_response_format
from quiz.validation.deduplication import DeduplicationValidator
from quiz.validation.distractor_consistency import DistractorConsistencyValidator
from quiz.validation.taxonomy_validator import TaxonomyValidator
from quiz.validation.validator import SymPyMathValidator


def _valid_question_dict(id_str: str = "q_test_1") -> dict:
    return {
        "id": id_str,
        "topic": "arithmetic",
        "subconcept": "order_of_operations",
        "question_text": "¿Cuánto es 5 + 3 * 4?",
        "options": {"A": "17", "B": "32", "C": "20", "D": "60"},
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "left_to_right_precedence",
                "explanation": "Sumaste antes de multiplicar.",
            },
            "C": {
                "misconception": "addition_before_multiplication",
                "explanation": "Sumaste antes de resolver la multiplicación.",
            },
            "D": {
                "misconception": "ignored_parentheses",
                "explanation": "Ignoraste el orden de precedencia.",
            },
        },
    }


def test_execute_llm_query_with_response_format():
    client = MockLLMClient(["response_text"])
    result = execute_llm_query(client, "system", "user", {"type": "json_object"})
    assert result == "response_text"
    assert len(client.call_history) == 1


def test_execute_llm_query_type_error_fallback():
    class LegacyClient(LLMClient):
        def __init__(self) -> None:
            self.called_without_format = False

        def generate(
            self,
            system_prompt: str,
            user_prompt: str,
            response_format: dict[str, Any] | None = None,
        ) -> str:
            if response_format is not None:
                raise TypeError("Unsupported response_format argument")
            self.called_without_format = True
            return "legacy_response"

    client = LegacyClient()
    result = execute_llm_query(
        client,
        "sys",
        "usr",
        {"type": "json_object"},
    )
    assert result == "legacy_response"
    assert client.called_without_format is True


def test_execute_generation_attempt_success():
    payload = _valid_question_dict()
    payload["derivation_scratchpad"] = "Target: 17\nEquation: 5 + 3 * 4"
    client = MockLLMClient([json.dumps(payload)])
    state = GenerationState("mock", "prompt", "prompt", max_retries=3)

    question = execute_generation_attempt(
        client=client,
        system_prompt="sys",
        base_user_prompt="prompt",
        response_format=build_quiz_response_format(),
        state=state,
        topic="arithmetic",
        subconcept="order_of_operations",
        question_id="q_test_1",
        math_validator=SymPyMathValidator(),
        taxonomy_validator=TaxonomyValidator(),
        dedup_validator=DeduplicationValidator(),
        distractor_validator=DistractorConsistencyValidator(),
    )
    assert question is not None
    assert question.id == "q_test_1"
    assert state.last_scratchpad is not None
    assert "Target: 17" in state.last_scratchpad


def test_execute_generation_attempt_json_parse_failure():
    client = MockLLMClient(["not valid json at all"])
    state = GenerationState("mock", "prompt", "prompt", max_retries=3)

    question = execute_generation_attempt(
        client=client,
        system_prompt="sys",
        base_user_prompt="prompt",
        response_format=build_quiz_response_format(),
        state=state,
        topic="arithmetic",
        subconcept="order_of_operations",
        question_id="q_test_1",
        math_validator=SymPyMathValidator(),
        taxonomy_validator=TaxonomyValidator(),
        dedup_validator=DeduplicationValidator(),
    )
    assert question is None
    assert state.attempt == 2
    assert len(state.accumulated_errors) == 1
    assert "Invalid JSON output" in state.accumulated_errors[0]


def test_execute_generation_attempt_validation_failure():
    payload = _valid_question_dict()
    payload["correct_option"] = "B"
    client = MockLLMClient([json.dumps(payload)])
    state = GenerationState("mock", "prompt", "prompt", max_retries=3)

    question = execute_generation_attempt(
        client=client,
        system_prompt="sys",
        base_user_prompt="prompt",
        response_format=build_quiz_response_format(),
        state=state,
        topic="arithmetic",
        subconcept="order_of_operations",
        question_id="q_test_1",
        math_validator=SymPyMathValidator(),
        taxonomy_validator=TaxonomyValidator(),
        dedup_validator=DeduplicationValidator(),
    )
    assert question is None
    assert state.attempt == 2
    assert len(state.accumulated_errors) >= 1
    assert any(
        "Schema violation" in err or "Distractor" in err
        for err in state.accumulated_errors
    )


def test_execute_generation_attempt_llm_failure():
    class BrokenClient:
        def generate(self, *args, **kwargs):
            raise ConnectionError("LLM offline")

    state = GenerationState("mock", "prompt", "prompt", max_retries=3)

    with pytest.raises(Exception) as exc_info:
        execute_generation_attempt(
            client=BrokenClient(),  # type: ignore[arg-type]
            system_prompt="sys",
            base_user_prompt="prompt",
            response_format=build_quiz_response_format(),
            state=state,
            topic="arithmetic",
            subconcept="order_of_operations",
            question_id="q_test_1",
            math_validator=SymPyMathValidator(),
            taxonomy_validator=TaxonomyValidator(),
            dedup_validator=DeduplicationValidator(),
        )
    assert "ConnectionError" in str(exc_info.value) or "LLM offline" in str(
        exc_info.value
    )
