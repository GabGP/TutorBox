"""FastAPI router for on-demand LLM diagnostic quiz question generation."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.quiz.dependencies import get_quiz_generator
from db.audit import record_audit
from db.database import get_db
from db.quiz import create_question, get_question_by_id
from db.quiz_telemetry import record_generation_log
from quiz.contracts.models import (
    GenerateQuestionRequest,
    GenerateQuestionResponse,
    QuizQuestionResponse,
)
from quiz.contracts.taxonomy import is_valid_subconcept, is_valid_topic
from quiz.generation.generator import GenerationError, QuizQuestionGenerator
from security import AuthContext, require_roles

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=GenerateQuestionResponse)
def generate_question(
    payload: GenerateQuestionRequest,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    generator: Annotated[QuizQuestionGenerator, Depends(get_quiz_generator)],
) -> GenerateQuestionResponse:
    """Generates a diagnostic quiz question on-demand via the rejection and retry pipeline."""
    # 1. Validate topic and subconcept against curriculum taxonomy
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

    # 2. Execute feedback-driven generation loop
    try:
        result = generator.generate(
            topic=payload.topic,
            subconcept=payload.subconcept,
        )
    except GenerationError as err:
        logger.error("Quiz generation failed: %s", err)
        # Persist failure telemetry record with rejection trail
        with get_db() as conn:
            record_generation_log(
                conn,
                user_id=ctx.user_id,
                topic=payload.topic,
                subconcept=payload.subconcept,
                model_name=err.model_name,
                attempts=err.attempts,
                duration_ms=err.duration_ms,
                success=False,
                question_id=None,
                rejection_history=err.accumulated_errors,
            )
            conn.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate valid quiz question: {err}",
        ) from err

    question = result.question
    saved_id: str | None = None
    created_at: str | None = None

    # 3. Optionally persist to question bank and record telemetry
    with get_db() as conn:
        if payload.save_to_bank:
            saved_id = create_question(
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
            saved_question = get_question_by_id(conn, saved_id)
            if saved_question is not None:
                created_at = saved_question.created_at

        # Log successful generation telemetry
        record_generation_log(
            conn,
            user_id=ctx.user_id,
            topic=payload.topic,
            subconcept=payload.subconcept,
            model_name=result.metadata.model_name,
            attempts=result.metadata.attempts,
            duration_ms=result.metadata.duration_ms,
            success=True,
            question_id=saved_id,
            rejection_history=result.metadata.rejection_history,
        )
        conn.commit()

    # 4. Return envelope containing question payload and telemetry metadata
    question_response = QuizQuestionResponse(
        id=saved_id or question.id,
        topic=question.topic,
        subconcept=question.subconcept,
        question_text=question.question_text,
        options=question.options,
        correct_option=question.correct_option,
        distractors=question.distractors,
        source="llm",
        sympy_verified=True,
        created_at=created_at,
    )
    return GenerateQuestionResponse(
        question=question_response,
        metadata=result.metadata,
    )
