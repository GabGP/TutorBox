"""Auth API package."""

from fastapi import APIRouter

from .login import (
    router as login_router,
)
from .logout import (
    router as logout_router,
)
from .schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
)

router = APIRouter()
router.include_router(login_router)
router.include_router(logout_router)

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "LogoutResponse",
    "login_router",
    "logout_router",
    "router",
]
