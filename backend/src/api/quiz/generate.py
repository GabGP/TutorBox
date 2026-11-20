"""FastAPI router for on-demand LLM diagnostic quiz question generation."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from api.quiz.dependencies import get_quiz_generator
from api.quiz.disconnect_watch import run_until_disconnected
from api.quiz.generate_store import generate_and_store
from core.security import AuthContext, require_roles
from modes.quiz.contracts.models import (
    GenerateQuestionRequest,
    GenerateQuestionResponse,
)
from modes.quiz.generation.generator import QuizQuestionGenerator
from modes.quiz.generation.types import GenerationCancelled

logger = logging.getLogger(__name__)
router = APIRouter()

# nginx's code for "client closed the request"; nobody is left to read it.
CLIENT_CLOSED_REQUEST = 499


@router.post("/generate", response_model=GenerateQuestionResponse)
async def generate_question(
    request: Request,
    payload: GenerateQuestionRequest,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    generator: Annotated[QuizQuestionGenerator, Depends(get_quiz_generator)],
) -> GenerateQuestionResponse:
    """Generates a question; stops between attempts once the client disconnects."""
    try:
        return await run_until_disconnected(
            request,
            lambda client_has_left: generate_and_store(
                payload, ctx, generator, client_has_left
            ),
        )
    except GenerationCancelled as cancelled:
        logger.info("Quiz generation stopped: the client disconnected.")
        raise HTTPException(
            status_code=CLIENT_CLOSED_REQUEST, detail="Generation stopped."
        ) from cancelled
