"""GET /api/v1/system/health: the Jetson's CPU, GPU, memory, temperatures, power and disk.

Teachers and admins only. The public watchdog check stays at GET /health (api/health.py).
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from core.security import AuthContext, require_roles
from core.system_health.factory import get_system_health_service
from core.system_health.models import SystemHealthSnapshot
from core.system_health.service import SystemHealthService

__all__ = ["router"]

router = APIRouter()

Staff = Annotated[AuthContext, Depends(require_roles("teacher", "admin"))]
HealthService = Annotated[SystemHealthService, Depends(get_system_health_service)]


@router.get("/health", response_model=SystemHealthSnapshot)
def jetson_health(_ctx: Staff, service: HealthService) -> SystemHealthSnapshot:
    """One sample of the appliance, read again at most every two seconds."""
    return service.snapshot()
