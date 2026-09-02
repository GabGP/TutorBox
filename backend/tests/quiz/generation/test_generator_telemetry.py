"""Unit tests for QuizQuestionGenerator telemetry, duration, attempts, and error tracking."""

import json

import pytest

from llm import LLMClient, MockLLMClient
from quiz.generation.generator import GenerationError, QuizQuestionGenerator
from quiz.validation.validator import SymPyMathValidator


def _valid_question_dict(id_str: str = "q_tel_1") -> dict:
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


def test_generator_one_shot_telemetry():
    """Verifies that a one-shot generation returns attempts=1 and duration_ms >= 0."""
    payload = _valid_question_dict()
    client = MockLLMClient([json.dumps(payload)], model="qwen2.5-coder-1.5b")
    generator = QuizQuestionGenerator(client)

    result = generator.generate("arithmetic", "order_of_operations")
    assert result.question.id == "q_tel_1"
    assert result.metadata.model_name == "qwen2.5-coder-1.5b"
    assert result.metadata.attempts == 1
    assert result.metadata.duration_ms >= 0.0
    assert result.metadata.rejection_history == []

    # Verify tuple unpacking and attribute delegation
    question, metadata = result
    assert question.id == "q_tel_1"
    assert metadata.attempts == 1
    assert result.id == "q_tel_1"
    assert result[0].id == "q_tel_1"
    assert result[1].attempts == 1


def test_generator_retry_telemetry_captures_rejections():
    """Verifies that intermediate rejection errors are captured in rejection_history."""
    invalid_schema = _valid_question_dict()
    del invalid_schema["distractors"]["B"]
    valid_payload = _valid_question_dict()

    class CustomNamedClient(LLMClient):
        def __init__(self, responses: list[str], model_name: str) -> None:
            self._responses = responses
            self._index = 0
            self.model_name: str = model_name

        def generate(self, system_prompt: str, user_prompt: str) -> str:
            resp = self._responses[self._index]
            self._index = min(self._index + 1, len(self._responses) - 1)
            return resp

    client = CustomNamedClient(
        [json.dumps(invalid_schema), json.dumps(valid_payload)],
        model_name="custom-slm-v1",
    )
    generator = QuizQuestionGenerator(client)

    result = generator.generate("arithmetic")
    assert result.metadata.model_name == "custom-slm-v1"
    assert result.metadata.attempts == 2
    assert result.metadata.duration_ms >= 0.0
    assert len(result.metadata.rejection_history) >= 1
    assert any("Schema violation" in err for err in result.metadata.rejection_history)


def test_generator_exhaustion_telemetry_in_generation_error():
    """Verifies that GenerationError contains attempts, duration, and error history."""

    class UnnamedLLM(LLMClient):
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            return "invalid json output"

    client = UnnamedLLM()
    generator = QuizQuestionGenerator(client)

    with pytest.raises(GenerationError) as exc_info:
        generator.generate("arithmetic", max_retries=3)

    err = exc_info.value
    assert err.attempts == 3
    assert err.duration_ms >= 0.0
    assert err.model_name == "unknown"
    assert len(err.accumulated_errors) == 3


def test_generator_llm_exception_telemetry():
    """Verifies that immediate SLM request exceptions attach attempt and timing metadata."""

    class CrashingLLM(MockLLMClient):
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            raise ConnectionRefusedError("LocalSLM offline")

    client = CrashingLLM(model="local-qwen")
    generator = QuizQuestionGenerator(client)

    with pytest.raises(GenerationError) as exc_info:
        generator.generate("arithmetic")

    err = exc_info.value
    assert err.attempts == 1
    assert err.duration_ms >= 0.0
    assert err.model_name == "local-qwen"
    assert err.accumulated_errors == []


def test_generator_retry_after_math_failure_telemetry():
    """Verifies math validation rejection tracking across retries."""
    invalid_math = _valid_question_dict()
    invalid_math["options"]["A"] = "99"
    valid_payload = _valid_question_dict()

    client = MockLLMClient([json.dumps(invalid_math), json.dumps(valid_payload)])
    generator = QuizQuestionGenerator(client, validator=SymPyMathValidator())

    result = generator.generate("arithmetic")
    assert result.metadata.attempts == 2
    assert any(
        "does not equal computed truth" in err
        for err in result.metadata.rejection_history
    )


def test_generator_max_retries_configured_from_environment(monkeypatch):
    """Verifies that QuizQuestionGenerator honors QUIZ_MAX_RETRIES environment variable."""
    monkeypatch.setenv("QUIZ_MAX_RETRIES", "2")
    client = MockLLMClient(["invalid json output"] * 5)
    generator = QuizQuestionGenerator(client)

    with pytest.raises(GenerationError) as exc_info:
        generator.generate("arithmetic")

    err = exc_info.value
    assert err.attempts == 2
    assert len(client.call_history) == 2
