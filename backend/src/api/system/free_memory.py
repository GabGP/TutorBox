"""POST /api/v1/system/free-memory: frees what the current classroom mode does not need right now.

Teachers and admins only. It answers with the RAM before and after and what each step did.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from core.security import AuthContext, require_roles
from core.system_health.factory import get_memory_releaser
from core.system_health.memory_release import MemoryReleaser
from core.system_health.release_report import MemoryReleaseReport

__all__ = ["router"]

router = APIRouter()

Staff = Annotated[AuthContext, Depends(require_roles("teacher", "admin"))]
Releaser = Annotated[MemoryReleaser, Depends(get_memory_releaser)]


@router.post("/free-memory", response_model=MemoryReleaseReport)
def free_memory(_ctx: Staff, releaser: Releaser) -> MemoryReleaseReport:
    """Unloads the models and voices the classroom is not using, then loads back only what the mode needs."""
    return releaser.release()
