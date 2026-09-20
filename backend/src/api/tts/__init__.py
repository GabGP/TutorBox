"""TTS lifecycle management API package."""

from fastapi import APIRouter

from api.tts.endpoints import router as endpoints_router
from api.tts.preview import router as preview_router

router = APIRouter()
router.include_router(endpoints_router)
router.include_router(preview_router)

__all__ = ["endpoints_router", "preview_router", "router"]
