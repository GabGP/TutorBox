"""Rate limiting package."""

from .lockout import (
    LOCKOUT_DURATION_SECONDS,
    MAX_ATTEMPTS,
    MAX_TRACKED_KEYS,
    InMemoryRateLimiter,
    check_rate_limit,
    login_rate_limiter,
)
from .sliding_window import (
    SIGNUP_MAX_EVENTS,
    SIGNUP_WINDOW_SECONDS,
    SlidingWindowLimiter,
    signup_rate_limiter,
)

__all__ = [
    "LOCKOUT_DURATION_SECONDS",
    "MAX_ATTEMPTS",
    "MAX_TRACKED_KEYS",
    "SIGNUP_MAX_EVENTS",
    "SIGNUP_WINDOW_SECONDS",
    "InMemoryRateLimiter",
    "SlidingWindowLimiter",
    "check_rate_limit",
    "login_rate_limiter",
    "signup_rate_limiter",
]
