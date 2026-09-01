"""Quiz API router package."""

from fastapi import APIRouter

from api.quiz.generate import router as generate_router
from api.quiz.questions_read import router as questions_read_router
from api.quiz.questions_write import router as questions_write_router
from api.quiz.schema import router as schema_router
from api.quiz.topics import router as topics_router
from api.quiz.validate import router as validate_router

router = APIRouter(prefix="/quiz")
router.include_router(topics_router)
router.include_router(schema_router)
router.include_router(validate_router)
router.include_router(generate_router)
router.include_router(questions_read_router)
router.include_router(questions_write_router)

__all__ = [
    "generate_router",
    "questions_read_router",
    "questions_write_router",
    "router",
    "schema_router",
    "topics_router",
    "validate_router",
]
