"""Hardware clicker transport (Week 7): ESP32 check-in and voting."""

from fastapi import APIRouter

from .checkin import router as checkin_router
from .vote import router as vote_router

router = APIRouter()
router.include_router(checkin_router)
router.include_router(vote_router)

__all__ = ["checkin_router", "router", "vote_router"]
