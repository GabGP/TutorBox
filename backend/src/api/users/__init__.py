"""Users API package."""

from fastapi import APIRouter

from .credentials import (
    ChangePinRequest,
    ChangeUsernameRequest,
    CredentialChangeResponse,
    _change_credential,
)
from .credentials import (
    router as credentials_router,
)
from .profile import UserProfileResponse
from .profile import router as profile_router
from .signup import SignupRequest, SignupResponse
from .signup import router as signup_router

router = APIRouter()
router.include_router(signup_router)
router.include_router(profile_router)
router.include_router(credentials_router)

__all__ = [
    "ChangePinRequest",
    "ChangeUsernameRequest",
    "CredentialChangeResponse",
    "SignupRequest",
    "SignupResponse",
    "UserProfileResponse",
    "_change_credential",
    "credentials_router",
    "profile_router",
    "router",
    "signup_router",
]
