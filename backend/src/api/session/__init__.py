"""Session API router package."""

from fastapi import APIRouter

from api.session.routes_host import router as host_router
from api.session.routes_participant import router as participant_router
from api.session.routes_report import router as report_router

router = APIRouter()
router.include_router(host_router)
router.include_router(participant_router)
router.include_router(report_router)

__all__ = ["host_router", "participant_router", "report_router", "router"]
