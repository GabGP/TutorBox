"""Staff API package."""

from fastapi import APIRouter

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

__all__ = [
    "CreateUserRequest",
    "CreateUserResponse",
    "UserListResponse",
    "router",
    "users_router",
]
