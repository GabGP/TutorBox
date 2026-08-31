"""FastAPI router for standalone mathematical and schema quiz validation."""

from typing import Annotated

from fastapi import APIRouter, Depends

from api.quiz.dependencies import get_math_validator
from quiz.contracts.models import MathValidationResult, ValidateQuestionRequest
from quiz.validation.validator import MathValidatorInterface

router = APIRouter()


@router.post("/validate", response_model=MathValidationResult)
def validate_question(
    payload: ValidateQuestionRequest,
    validator: Annotated[MathValidatorInterface, Depends(get_math_validator)],
) -> MathValidationResult:
    """Validates a quiz question for mathematical accuracy and distractor correctness."""
    return validator.validate_question_math(payload.question)
