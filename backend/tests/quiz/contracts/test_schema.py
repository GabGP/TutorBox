import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.quiz.contracts.schema import (
    JSON_SCHEMA_DRAFT,
    SCHEMA_ID,
    SCHEMA_VERSION,
    export_quiz_question_schema,
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


def test_schema_constants_and_metadata():
    assert SCHEMA_VERSION == "1.0.0"
    assert SCHEMA_ID == "https://tutorbox.local/schemas/v1/quiz_question.schema.json"
    assert JSON_SCHEMA_DRAFT == "https://json-schema.org/draft/2020-12/schema"

    schema = get_quiz_question_json_schema()
    assert isinstance(schema, dict)
    assert schema["$schema"] == JSON_SCHEMA_DRAFT
    assert schema["$id"] == SCHEMA_ID
    assert schema["version"] == SCHEMA_VERSION
    assert schema["title"] == "QuizQuestion"
    assert "description" in schema
    assert "properties" in schema
    assert "options" in schema["properties"]
    assert "distractors" in schema["properties"]
    assert "correct_option" in schema["properties"]
    assert "schema_version" in schema["properties"]


def test_get_quiz_question_schema_json():
    schema_str = get_quiz_question_schema_json()
    parsed = json.loads(schema_str)
    assert parsed["title"] == "QuizQuestion"
    assert parsed["version"] == "1.0.0"


def test_export_quiz_question_schema(tmp_path: Path):
    export_destination = tmp_path / "schemas" / "quiz_question.schema.json"
    exported_path = export_quiz_question_schema(export_destination)

    assert exported_path == export_destination
    assert exported_path.exists()
    content = exported_path.read_text(encoding="utf-8")
    expected_content = f"{get_quiz_question_schema_json(indent=2)}\n"
    assert content == expected_content


def test_anti_drift_static_schema_file():
    """Anti-drift CI gate: ensures backend/schemas/v1/quiz_question.schema.json matches code schema."""
    backend_root = Path(__file__).resolve().parents[3]
    static_schema_path = backend_root / "schemas" / "v1" / "quiz_question.schema.json"

    assert static_schema_path.exists(), (
        f"Static schema file missing at {static_schema_path}"
    )

    disk_content = static_schema_path.read_text(encoding="utf-8")
    code_generated_content = f"{get_quiz_question_schema_json(indent=2)}\n"
    assert disk_content == code_generated_content, (
        "Anti-drift failure: static schema file does not match Pydantic model contract. "
        "Run export_quiz_question_schema() to update."
    )


def test_validate_quiz_question_dict_valid():
    data = sample_dict()
    q = validate_quiz_question_dict(data)
    assert q.id == "q_math_002"
    assert q.correct_option == "A"
    assert q.options["A"] == "3/4"
    assert q.schema_version == "1.0.0"


def test_validate_quiz_question_dict_invalid():
    data = sample_dict()
    data.pop("distractors")
    with pytest.raises(ValidationError):
        validate_quiz_question_dict(data)
