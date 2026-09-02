"""Centralized API routing topology for TutorBox."""

from fastapi import APIRouter

from api.auth import router as auth_router
from api.health import router as health_router
from api.quiz import router as quiz_router
from api.staff import router as staff_router
from api.users import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router, prefix="/auth")
api_v1_router.include_router(users_router, prefix="/users")
api_v1_router.include_router(staff_router, prefix="/staff")
api_v1_router.include_router(quiz_router, prefix="/quiz")

root_router = APIRouter()
root_router.include_router(health_router)
root_router.include_router(api_v1_router)

__all__ = ["api_v1_router", "root_router"]
