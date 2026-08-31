"""FastAPI router for on-demand LLM diagnostic quiz question generation."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.quiz.dependencies import get_quiz_generator
from db.audit import record_audit
from db.database import get_db
from db.quiz import create_question, get_question_by_id
from quiz.contracts.models import GenerateQuestionRequest, QuizQuestionResponse
from quiz.contracts.taxonomy import is_valid_subconcept, is_valid_topic
from quiz.generation.generator import GenerationError, QuizQuestionGenerator
from security import AuthContext, require_roles

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=QuizQuestionResponse)
def generate_question(
    payload: GenerateQuestionRequest,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    generator: Annotated[QuizQuestionGenerator, Depends(get_quiz_generator)],
) -> QuizQuestionResponse:
    """Generates a diagnostic quiz question on-demand via the rejection and retry pipeline."""
    if not is_valid_topic(payload.topic):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid topic: '{payload.topic}'.",
        )
    if payload.subconcept and not is_valid_subconcept(
        payload.topic, payload.subconcept
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Invalid subconcept: '{payload.subconcept}' "
                f"for topic '{payload.topic}'."
            ),
        )

    try:
        question = generator.generate(
            topic=payload.topic,
            subconcept=payload.subconcept,
        )
    except GenerationError as err:
        logger.error("Quiz generation failed: %s", err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate valid quiz question: {err}",
        ) from err

    if payload.save_to_bank:
        with get_db() as conn:
            question_id = create_question(
                conn,
                question=question,
                source="llm",
                sympy_verified=True,
            )
            record_audit(
                conn,
                actor_user_id=ctx.user_id,
                action="quiz_question_generated",
                target_user_id=None,
            )
            conn.commit()
            saved_question = get_question_by_id(conn, question_id)
            if saved_question is not None:
                return saved_question

    return QuizQuestionResponse(
        id=question.id,
        topic=question.topic,
        subconcept=question.subconcept,
        question_text=question.question_text,
        options=question.options,
        correct_option=question.correct_option,
        distractors=question.distractors,
        source="llm",
        sympy_verified=True,
    )
