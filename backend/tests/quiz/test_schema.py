import json

import pytest
from pydantic import ValidationError

from src.quiz.schema import (
    get_quiz_question_json_schema,
    get_quiz_question_schema_json,
    validate_quiz_question_dict,
)


def sample_dict() -> dict:
    return {
        "id": "q_math_002",
        "topic": "fractions",
        "subconcept": "addition_subtraction",
        "question_text": "¿Cuánto es 1/4 + 2/4?",
        "options": {"A": "3/4", "B": "3/8", "C": "2/4", "D": "1/8"},
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "added_denominators",
                "explanation": "Sumaste los denominadores 4 + 4 = 8 en vez de mantener el 4.",
            },
            "C": {
                "misconception": "ignored_addition",
                "explanation": "Mantuviste el numerador 2 sin sumar el 1.",
            },
            "D": {
                "misconception": "subtracted_instead",
                "explanation": "Restaste los numeradores en lugar de sumarlos.",
            },
        },
    }


def test_get_quiz_question_json_schema():
    schema = get_quiz_question_json_schema()
    assert isinstance(schema, dict)
    assert "properties" in schema
    assert "options" in schema["properties"]
    assert "distractors" in schema["properties"]
    assert "correct_option" in schema["properties"]


def test_get_quiz_question_schema_json():
    schema_str = get_quiz_question_schema_json()
    parsed = json.loads(schema_str)
    assert parsed["title"] == "QuizQuestion"


def test_validate_quiz_question_dict_valid():
    data = sample_dict()
    q = validate_quiz_question_dict(data)
    assert q.id == "q_math_002"
    assert q.correct_option == "A"
    assert q.options["A"] == "3/4"


def test_validate_quiz_question_dict_invalid():
    data = sample_dict()
    data.pop("distractors")
    with pytest.raises(ValidationError):
        validate_quiz_question_dict(data)
