"""FastAPI router for quiz question bank create and delete operations."""

import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.quiz.dependencies import get_math_validator
from db.audit import record_audit
from db.database import get_db
from db.quiz import create_question, get_question_by_id, soft_delete_question
from quiz.contracts.models import (
    QuizDeleteResponse,
    QuizQuestionCreate,
    QuizQuestionResponse,
)
from quiz.contracts.taxonomy import is_valid_subconcept, is_valid_topic
from quiz.validation.validator import MathValidatorInterface
from security import AuthContext, require_roles

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/questions",
    response_model=QuizQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz_question(
    payload: QuizQuestionCreate,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    validator: Annotated[MathValidatorInterface, Depends(get_math_validator)],
) -> QuizQuestionResponse:
    """Manually creates a new verified diagnostic question in the question bank."""
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

    try:
        with get_db() as conn:
            question_id = create_question(
                conn,
                question=payload,
                source="teacher",
                sympy_verified=True,
            )
            record_audit(
                conn,
                actor_user_id=ctx.user_id,
                action="quiz_question_created",
                target_user_id=None,
            )
            conn.commit()
            created = get_question_by_id(conn, question_id)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Question with ID '{payload.id}' already exists.",
        )

    if created is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created question.",
        )
    return created


@router.delete("/questions/{question_id}", response_model=QuizDeleteResponse)
def delete_question(
    question_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
) -> QuizDeleteResponse:
    """Soft deletes a question from the question bank."""
    with get_db() as conn:
        deleted = soft_delete_question(conn, question_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question '{question_id}' not found or already deleted.",
            )
        record_audit(
            conn,
            actor_user_id=ctx.user_id,
            action="quiz_question_deleted",
            target_user_id=None,
        )
        conn.commit()
    return QuizDeleteResponse(detail="Question deleted.")
