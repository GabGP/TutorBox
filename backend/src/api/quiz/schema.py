"""FastAPI router for quiz question JSON schema contract."""

from typing import Any

from fastapi import APIRouter

from quiz.contracts.schema import get_quiz_question_json_schema

router = APIRouter()


@router.get("/schema", response_model=dict[str, Any])
def get_quiz_schema() -> dict[str, Any]:
    """Returns canonical versioned JSON Schema (Draft 2020-12) for diagnostic quiz questions."""
    return get_quiz_question_json_schema()
