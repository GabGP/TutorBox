"""FastAPI router for quiz question bank read operations."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from db.database import get_db
from db.quiz import count_questions, get_question_by_id, list_questions
from quiz.contracts.models import QuestionListResponse, QuizQuestionResponse
from security import AuthContext, require_roles

logger = logging.getLogger(__name__)
DEFAULT_QUESTION_LIMIT: int = 50
MAX_QUESTION_LIMIT: int = 200

router = APIRouter()


@router.get("/questions", response_model=QuestionListResponse)
def get_questions(
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    topic: str | None = None,
    subconcept: str | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_QUESTION_LIMIT)] = DEFAULT_QUESTION_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
    include_deleted: bool = False,
) -> QuestionListResponse:
    """Lists quiz questions from the bank with optional filtering and pagination."""
    with get_db() as conn:
        questions = list_questions(
            conn,
            topic=topic,
            subconcept=subconcept,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
        total = count_questions(
            conn,
            topic=topic,
            subconcept=subconcept,
            include_deleted=include_deleted,
        )
    return QuestionListResponse(questions=questions, total=total)


@router.get("/questions/{question_id}", response_model=QuizQuestionResponse)
def get_question(
    question_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    include_deleted: bool = False,
) -> QuizQuestionResponse:
    """Retrieves a single quiz question by ID."""
    with get_db() as conn:
        question = get_question_by_id(
            conn, question_id=question_id, include_deleted=include_deleted
        )
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{question_id}' not found.",
        )
    return question
