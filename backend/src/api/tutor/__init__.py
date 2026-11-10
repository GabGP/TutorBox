"""Mode 2 API package: the Socratic math tutor chat and its teacher report."""

from fastapi import APIRouter

from api.tutor.analytics import router as analytics_router
from api.tutor.endpoints import router as chat_router

router = APIRouter()
router.include_router(chat_router)
router.include_router(analytics_router)

__all__ = ["router"]
