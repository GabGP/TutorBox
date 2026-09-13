"""Session API router package."""

from fastapi import APIRouter

from api.session.host import router as host_router
from api.session.participant import router as participant_router
from api.session.reports import router as report_router
from api.session.speech import router as speech_router

router = APIRouter()
router.include_router(host_router)
router.include_router(participant_router)
router.include_router(report_router)
router.include_router(speech_router)

__all__ = [
    "host_router",
    "participant_router",
    "report_router",
    "router",
    "speech_router",
]
