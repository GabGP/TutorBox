import json

import pytest

from src.quiz.generation.generator import GenerationError, QuizQuestionGenerator
from src.quiz.generation.llm_client import MockLLMClient
from src.quiz.validation.validator import SymPyMathValidator


def valid_question_dict(id_str: str = "q_test_1") -> dict:
    return {
        "id": id_str,
        "topic": "arithmetic",
        "subconcept": "order_of_operations",
        "question_text": "¿Cuánto es 3 + 4 * 2?",
        "options": {"A": "11", "B": "14", "C": "10", "D": "24"},
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "left_to_right_precedence",
                "explanation": "Sumaste antes de multiplicar.",
            },
            "C": {
                "misconception": "multiplication_error",
                "explanation": "Multiplicaste mal.",
            },
            "D": {
                "misconception": "multiplied_all",
                "explanation": "Multiplicaste todo.",
            },
        },
    }


def test_generator_one_shot_success():
    payload = valid_question_dict()
    client = MockLLMClient([json.dumps(payload)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic", "order_of_operations")
    assert question.id == "q_test_1"
    assert question.correct_option == "A"
    assert len(client.call_history) == 1


def test_generator_markdown_fence_extraction():
    payload = valid_question_dict()
    fenced = f"```json\n{json.dumps(payload)}\n```"
    client = MockLLMClient([fenced])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
    assert question.options["A"] == "11"


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
    del invalid_schema["distractors"]["B"]  # Only 2 distractors
    valid_payload = valid_question_dict()

    client = MockLLMClient([json.dumps(invalid_schema), json.dumps(valid_payload)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
    assert len(client.call_history) == 2
    assert "Schema violation" in client.call_history[1][1]


def test_generator_retry_after_math_failure():
    invalid_math = valid_question_dict()
    invalid_math["options"]["A"] = (
        "14"  # Marked correct A is mathematically wrong (14 != 11)
    )
    invalid_math["options"]["B"] = "12"
    valid_payload = valid_question_dict()

    client = MockLLMClient([json.dumps(invalid_math), json.dumps(valid_payload)])
    generator = QuizQuestionGenerator(client, validator=SymPyMathValidator())

    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
    assert len(client.call_history) == 2
    assert "does not equal computed truth" in client.call_history[1][1]


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


def test_generator_auto_assign_custom_id():
    payload = valid_question_dict()
    del payload["id"]
    client = MockLLMClient([json.dumps(payload)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic", question_id="custom_id_123")
    assert question.id == "custom_id_123"


def test_generator_auto_assign_uuid_when_no_id():
    payload = valid_question_dict()
    del payload["id"]
    client = MockLLMClient([json.dumps(payload)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic")
    assert question.id.startswith("q_gen_")


def test_generator_nested_json_extraction_with_commentary():
    payload = valid_question_dict()
    raw_llm = (
        "Here is the generated question:\n"
        f"```json\n{json.dumps(payload, indent=2)}\n```\n"
        "Hope this is useful for class!"
    )
    client = MockLLMClient([raw_llm])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
    assert question.options["A"] == "11"
    assert len(question.distractors) == 3


def test_generator_llm_request_failure_raises_generation_error():
    class FailingLLMClient(MockLLMClient):
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            raise RuntimeError("Connection refused")

    client = FailingLLMClient()
    generator = QuizQuestionGenerator(client)
    with pytest.raises(GenerationError, match="SLM completion request failed"):
        generator.generate("arithmetic")
