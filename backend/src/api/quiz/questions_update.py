"""FastAPI router for quiz question bank update operations."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.quiz.dependencies import get_math_validator
from core.db.audit import record_audit
from core.db.database import get_db
from core.db.question_repository import get_question_by_id
from core.db.question_update import update_question
from core.security import AuthContext, require_roles
from modes.quiz.contracts.models import QuizQuestionCreate, QuizQuestionResponse
from modes.quiz.contracts.taxonomy import is_valid_subconcept, is_valid_topic
from modes.quiz.validation.validator import MathValidatorInterface

logger = logging.getLogger(__name__)
router = APIRouter()


@router.put("/questions/{question_id}", response_model=QuizQuestionResponse)
def update_quiz_question(
    question_id: str,
    payload: QuizQuestionCreate,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    validator: Annotated[MathValidatorInterface, Depends(get_math_validator)],
) -> QuizQuestionResponse:
    """Edits a live bank question after taxonomy and math re-validation."""
    if not is_valid_topic(payload.topic):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid topic: '{payload.topic}'.",
        )
    if not is_valid_subconcept(payload.topic, payload.subconcept):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Invalid subconcept: '{payload.subconcept}' "
                f"for topic '{payload.topic}'."
            ),
        )

    math_result = validator.validate_question_math(payload)
    if not math_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Mathematical validation failed: {'; '.join(math_result.errors)}",
        )

    with get_db() as conn:
        updated = update_question(
            conn,
            question_id,
            question=payload,
            source="teacher",
            sympy_verified=True,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question '{question_id}' not found or already deleted.",
            )
        record_audit(
            conn,
            actor_user_id=ctx.user_id,
            action="quiz_question_updated",
            target_user_id=None,
        )
        conn.commit()
        refreshed = get_question_by_id(conn, question_id)

    if refreshed is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated question.",
        )
    return refreshed
