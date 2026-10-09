"""Mode 3 API package: game event ingestion from the grade apps, and its summary for staff."""

from fastapi import APIRouter

from api.games.endpoints import router as events_router
from api.games.summary import router as summary_router

router = APIRouter()
router.include_router(events_router)
router.include_router(summary_router)

__all__ = ["events_router", "router", "summary_router"]
