import json
from pathlib import Path
from typing import Any

from quiz.contracts.models import QuizQuestion

SCHEMA_VERSION: str = "1.0.0"
SCHEMA_ID: str = "https://tutorbox.local/schemas/v1/quiz_question.schema.json"
JSON_SCHEMA_DRAFT: str = "https://json-schema.org/draft/2020-12/schema"


def get_quiz_question_json_schema() -> dict[str, Any]:
    """Generates canonical standard JSON Schema specification for QuizQuestion."""
    schema_definition: dict[str, Any] = QuizQuestion.model_json_schema()
    schema_definition["$schema"] = JSON_SCHEMA_DRAFT
    schema_definition["$id"] = SCHEMA_ID
    schema_definition["version"] = SCHEMA_VERSION
    schema_definition["title"] = "QuizQuestion"
    schema_definition["description"] = (
        "Canonical versioned contract schema for TutorBox diagnostic multiple-choice quiz questions."
    )
    return schema_definition


def get_quiz_question_schema_json(indent: int = 2) -> str:
    """Returns JSON string representation of the QuizQuestion schema."""
    return json.dumps(get_quiz_question_json_schema(), indent=indent)


def export_quiz_question_schema(output_path: Path | str) -> Path:
    """Exports the canonical QuizQuestion JSON Schema to the specified file path."""
    target_destination_path = Path(output_path)
    target_destination_path.parent.mkdir(parents=True, exist_ok=True)
    schema_content_json = get_quiz_question_schema_json(indent=2)
    target_destination_path.write_text(f"{schema_content_json}\n", encoding="utf-8")
    return target_destination_path


def validate_quiz_question_dict(data: dict[str, Any]) -> QuizQuestion:
    """
    Validates a raw dictionary against the QuizQuestion schema.
    Raises pydantic.ValidationError if invalid.
    """
    return QuizQuestion.model_validate(data)
