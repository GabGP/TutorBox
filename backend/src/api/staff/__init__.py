"""Staff API package."""

from fastapi import APIRouter

from .audit import (
    AuditLogsResponse,
)
from .audit import (
    router as audit_router,
)
from .delete import (
    DeleteUserResponse,
)
from .delete import (
    router as delete_router,
)
from .recover import (
    RecoverUserRequest,
    RecoverUserResponse,
)
from .recover import (
    router as recover_router,
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
router.include_router(delete_router)
router.include_router(recover_router)
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
    "delete_router",
    "recover_router",
    "reset_pin_router",
    "router",
    "users_router",
]
