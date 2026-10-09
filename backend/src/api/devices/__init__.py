"""Clicker API package: ESP32 clickers trade their secret for a student's login."""

from fastapi import APIRouter

from api.devices.auth import router as auth_router

router = APIRouter()
router.include_router(auth_router)

__all__ = ["auth_router", "router"]
