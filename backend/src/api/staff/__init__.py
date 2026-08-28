"""Staff API package."""

from fastapi import APIRouter

from .audit import (
    AuditLogsResponse,
)
from .audit import (
    router as audit_router,
)
from .lifecycle import (
    DeleteUserResponse,
    RecoverUserRequest,
    RecoverUserResponse,
)
from .lifecycle import (
    router as lifecycle_router,
)
from .reset_pin import (
    ResetPinResponse,
)
from .reset_pin import (
    router as reset_pin_router,
)
from .users import (
    CreateUserRequest,
    CreateUserResponse,
    UserListResponse,
)
from .users import (
    router as users_router,
)

router = APIRouter()
router.include_router(users_router)
router.include_router(reset_pin_router)
router.include_router(lifecycle_router)
router.include_router(audit_router)

__all__ = [
    "AuditLogsResponse",
    "CreateUserRequest",
    "CreateUserResponse",
    "DeleteUserResponse",
    "RecoverUserRequest",
    "RecoverUserResponse",
    "ResetPinResponse",
    "UserListResponse",
    "audit_router",
    "lifecycle_router",
    "reset_pin_router",
    "router",
    "users_router",
]
