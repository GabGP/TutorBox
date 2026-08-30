import json
from typing import Any

from quiz.models import QuizQuestion


def get_quiz_question_json_schema() -> dict[str, Any]:
    """Generates standard JSON Schema specification for QuizQuestion."""
    return QuizQuestion.model_json_schema()


def get_quiz_question_schema_json(indent: int = 2) -> str:
    """Returns JSON string representation of the QuizQuestion schema."""
    return json.dumps(get_quiz_question_json_schema(), indent=indent)


def validate_quiz_question_dict(data: dict[str, Any]) -> QuizQuestion:
    """
    Validates a raw dictionary against the QuizQuestion schema.
    Raises pydantic.ValidationError if invalid.
    """
    return QuizQuestion.model_validate(data)
