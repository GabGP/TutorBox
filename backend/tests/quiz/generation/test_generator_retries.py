"""Unit tests for QuizQuestionGenerator rejection and retry recovery cycles."""

import json

import pytest

from llm import MockLLMClient
from quiz.generation.generator import GenerationError, QuizQuestionGenerator
from quiz.validation.validator import SymPyMathValidator


def valid_question_dict(id_str: str = "q_test_1") -> dict:
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


def _valid_algebra_dict(id_str: str = "q_test_algebra") -> dict:
    return {
        "id": id_str,
        "topic": "pre_algebra",
        "subconcept": "two_step_equations",
        "question_text": "¿Cuál es el valor de x en 7*x - 5 = 30?",
        "options": {"A": "5", "B": "35", "C": "2", "D": "25"},
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "forgot_division",
                "explanation": "Olvidaste dividir.",
            },
            "C": {
                "misconception": "subtracted_instead_of_divided",
                "explanation": "Restaste en vez de dividir.",
            },
            "D": {
                "misconception": "divided_before_subtracting",
                "explanation": "Dividiste antes de restar.",
            },
        },
    }


def test_generator_retry_after_malformed_json():
    payload = valid_question_dict()
    malformed = "Aquí está tu pregunta: { id: invalid json..."
    client = MockLLMClient([malformed, json.dumps(payload)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
    assert len(client.call_history) == 2
    assert "ATTENTION: Your previous response was rejected" in client.call_history[1][1]


def test_generator_retry_after_schema_violation():
    invalid_schema = valid_question_dict()
    del invalid_schema["distractors"]["B"]
    valid_payload = valid_question_dict()

    client = MockLLMClient([json.dumps(invalid_schema), json.dumps(valid_payload)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
    assert len(client.call_history) == 2
    assert "Schema violation" in client.call_history[1][1]


def test_generator_retry_after_math_failure():
    invalid_math = valid_question_dict()
    invalid_math["options"]["A"] = "32"
    invalid_math["options"]["B"] = "12"
    valid_payload = valid_question_dict()

    client = MockLLMClient([json.dumps(invalid_math), json.dumps(valid_payload)])
    generator = QuizQuestionGenerator(client, validator=SymPyMathValidator())

    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
    assert len(client.call_history) == 2
    assert "does not equal computed truth" in client.call_history[1][1]
    assert "CRITICAL REVISION RULE" in client.call_history[1][1]


def test_generator_retry_after_distractor_boilerplate_failure():
    boilerplate_payload = valid_question_dict("q_fail_bp")
    boilerplate_payload["distractors"]["B"]["explanation"] = (
        "Al realizar la operación, obtendrías la respuesta B."
    )
    valid_payload = valid_question_dict("q_succ_bp")

    client = MockLLMClient([json.dumps(boilerplate_payload), json.dumps(valid_payload)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic")
    assert question.id == "q_succ_bp"
    assert len(client.call_history) == 2
    retry_prompt = client.call_history[1][1]
    assert "empty boilerplate" in retry_prompt
    assert "CRITICAL REVISION RULE" in retry_prompt
    assert "backward formulation" in retry_prompt


def test_generator_retry_after_duplicate_seed_question():
    duplicate_seed = _valid_algebra_dict("q_dup")
    duplicate_seed["question_text"] = "¿Cuál es el valor de x en: 2*x + 4 = 12?"
    duplicate_seed["options"] = {"A": "4", "B": "8", "C": "2", "D": "6"}
    valid_unique = _valid_algebra_dict()
    client = MockLLMClient([json.dumps(duplicate_seed), json.dumps(valid_unique)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("pre_algebra", "two_step_equations")
    assert question.id == "q_test_algebra"
    assert len(client.call_history) == 2
    assert "duplicates an existing question in the bank" in client.call_history[1][1]


def test_generator_exhaustion_raises_generation_error():
    client = MockLLMClient(["invalid json output"] * 3)
    generator = QuizQuestionGenerator(client)

    with pytest.raises(
        GenerationError, match="Failed to generate a valid quiz question"
    ):
        generator.generate("arithmetic", max_retries=3)
    assert len(client.call_history) == 3


def test_generator_non_dict_json_recovery():
    array_json = "[1, 2, 3]"
    valid_payload = valid_question_dict()

    client = MockLLMClient([array_json, json.dumps(valid_payload)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
    assert len(client.call_history) == 2


def test_generator_retry_after_taxonomy_topic_mismatch():
    drifted_payload = valid_question_dict()
    drifted_payload["topic"] = "arithmetic"
    valid_algebra = _valid_algebra_dict()
    client = MockLLMClient([json.dumps(drifted_payload), json.dumps(valid_algebra)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("pre_algebra", "two_step_equations")
    assert question.id == "q_test_algebra"
    assert len(client.call_history) == 2
    assert "Topic mismatch: requested 'pre_algebra'" in client.call_history[1][1]


def test_generator_retry_after_taxonomy_misconception_mismatch():
    invalid_misc = _valid_algebra_dict("q_test_bad_misc")
    invalid_misc["distractors"]["B"]["misconception"] = "multiplied_all"
    valid_algebra = _valid_algebra_dict("q_test_algebra_ok")

    client = MockLLMClient([json.dumps(invalid_misc), json.dumps(valid_algebra)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("pre_algebra", "two_step_equations")
    assert question.id == "q_test_algebra_ok"
    assert len(client.call_history) == 2
    assert "Misconception 'multiplied_all'" in client.call_history[1][1]


def test_generator_llm_request_failure_raises_generation_error():
    class FailingLLMClient(MockLLMClient):
        def generate(
            self,
            system_prompt: str,
            user_prompt: str,
            response_format: dict | None = None,
        ) -> str:
            raise RuntimeError("Connection refused")

    client = FailingLLMClient()
    generator = QuizQuestionGenerator(client)
    with pytest.raises(GenerationError, match="SLM completion request failed"):
        generator.generate("arithmetic")
