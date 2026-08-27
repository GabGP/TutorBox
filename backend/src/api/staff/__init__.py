"""Staff API package."""

from fastapi import APIRouter

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

__all__ = [
    "CreateUserRequest",
    "CreateUserResponse",
    "ResetPinResponse",
    "UserListResponse",
    "reset_pin_router",
    "router",
    "users_router",
]
