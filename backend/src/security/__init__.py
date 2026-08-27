"""TutorBox Security package."""

from . import auth, rate_limit, session, validation
from .auth import hash_pin, verify_pin
from .rate_limit import (
    InMemoryRateLimiter,
    SlidingWindowLimiter,
    check_rate_limit,
    login_rate_limiter,
    signup_rate_limiter,
)
from .session import (
    AuthContext,
    ensure_no_pending_rotation,
    get_current_session,
    require_roles,
)
from .validation import (
    ALLOWED_ROLES,
    PIN_MAX_LENGTH,
    PIN_MIN_LENGTH,
    PIN_PATTERN,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_PATTERN,
    PinField,
    RoleField,
    UsernameField,
)

__all__ = [
    "ALLOWED_ROLES",
    "PIN_MAX_LENGTH",
    "PIN_MIN_LENGTH",
    "PIN_PATTERN",
    "USERNAME_MAX_LENGTH",
    "USERNAME_MIN_LENGTH",
    "USERNAME_PATTERN",
    "AuthContext",
    "InMemoryRateLimiter",
    "PinField",
    "RoleField",
    "SlidingWindowLimiter",
    "UsernameField",
    "auth",
    "check_rate_limit",
    "ensure_no_pending_rotation",
    "get_current_session",
    "hash_pin",
    "login_rate_limiter",
    "rate_limit",
    "require_roles",
    "session",
    "signup_rate_limiter",
    "validation",
    "verify_pin",
]
