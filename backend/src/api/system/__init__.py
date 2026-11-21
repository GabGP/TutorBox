"""System API package: the Jetson health panel's data and its memory release, for staff."""

from fastapi import APIRouter

from api.system.free_memory import router as free_memory_router
from api.system.health import router as health_router

router = APIRouter()
router.include_router(health_router)
router.include_router(free_memory_router)

__all__ = ["router"]
