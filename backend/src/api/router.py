"""Centralized API routing topology for TutorBox."""

from fastapi import APIRouter

from api.auth import router as auth_router
from api.captive import router as captive_router
from api.health import router as health_router
from api.llm import router as llm_router
from api.mode import router as mode_router
from api.quiz import router as quiz_router
from api.session import router as session_router
from api.staff import router as staff_router
from api.tts import router as tts_router
from api.users import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router, prefix="/auth")
api_v1_router.include_router(users_router, prefix="/users")
api_v1_router.include_router(staff_router, prefix="/staff")
api_v1_router.include_router(quiz_router, prefix="/quiz")
api_v1_router.include_router(session_router, prefix="/session")
api_v1_router.include_router(tts_router, prefix="/tts")
api_v1_router.include_router(llm_router, prefix="/llm")
api_v1_router.include_router(mode_router, prefix="/mode")

root_router = APIRouter()
root_router.include_router(health_router)
root_router.include_router(captive_router)
root_router.include_router(api_v1_router)

__all__ = ["api_v1_router", "root_router"]
