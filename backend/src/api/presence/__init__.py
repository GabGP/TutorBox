"""Presence API package: the connection heartbeat and the teacher's class view."""

from fastapi import APIRouter

from api.presence.class_view import router as class_view_router
from api.presence.heartbeat import router as heartbeat_router

router = APIRouter()
router.include_router(heartbeat_router)
router.include_router(class_view_router)

__all__ = ["class_view_router", "heartbeat_router", "router"]
