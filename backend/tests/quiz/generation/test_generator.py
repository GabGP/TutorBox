"""Unit tests for QuizQuestionGenerator one-shot generation and output processing."""

import json

from llm import LLMClient, MockLLMClient
from quiz.generation.generator import QuizQuestionGenerator


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


def test_generator_one_shot_success():
    payload = valid_question_dict()
    client = MockLLMClient([json.dumps(payload)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic", "order_of_operations")
    assert question.id == "q_test_1"
    assert question.options[question.correct_option] == "17"
    assert question.correct_option in {"A", "B", "C", "D"}
    assert len(client.call_history) == 1
    assert len(client.recorded_response_formats) == 1
    assert client.recorded_response_formats[0] is not None
    assert client.recorded_response_formats[0]["type"] == "json_schema"


def test_generator_markdown_fence_extraction():
    payload = valid_question_dict()
    fenced = f"```json\n{json.dumps(payload)}\n```"
    client = MockLLMClient([fenced])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
    assert question.options[question.correct_option] == "17"
    assert set(question.options.values()) == {"17", "32", "20", "60"}


def test_generator_think_tag_sanitization():
    payload = valid_question_dict()
    reasoning_output = (
        f"<think>\nSolving 5 + 4 * 3 = 17.\n"
        f"Let's format JSON: {{...}}\n</think>\n"
        f"```json\n{json.dumps(payload)}\n```"
    )
    client = MockLLMClient([reasoning_output])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
    assert question.options[question.correct_option] == "17"


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
    assert question.options[question.correct_option] == "17"
    assert len(question.distractors) == 3


def test_generator_auto_sanitizes_latex_math_delimiters():
    payload_with_latex = {
        "id": "q_latex_gen",
        "topic": "pre_algebra",
        "subconcept": "two_step_equations",
        "question_text": "¿Cuál es el valor de $x$ en $7*x - 5 = 30$?",
        "options": {"A": "$5$", "B": "$35$", "C": "$2$", "D": "$25$"},
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "forgot_division",
                "explanation": "Olvidaste dividir por $7$.",
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
    client = MockLLMClient([json.dumps(payload_with_latex)])
    generator = QuizQuestionGenerator(client)

    question = generator.generate("pre_algebra", "two_step_equations")
    assert question.id == "q_latex_gen"
    assert question.question_text == "¿Cuál es el valor de x en 7*x - 5 = 30?"
    assert "$" not in question.question_text
    assert question.options[question.correct_option] == "5"
    assert set(question.options.values()) == {"5", "35", "2", "25"}
    assert all("$" not in opt for opt in question.options.values())
    assert all("$" not in dist.explanation for dist in question.distractors.values())


def test_generator_handles_legacy_2_arg_llm_client():
    payload = valid_question_dict()

    class LegacyClient(LLMClient):
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            return json.dumps(payload)

    generator = QuizQuestionGenerator(LegacyClient())
    question = generator.generate("arithmetic")
    assert question.id == "q_test_1"
