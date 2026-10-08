"""The login lockout instance and the 429 guard the auth routes call before a PIN check."""

import logging

from fastapi import HTTPException, Request, status

from .lockout import InMemoryRateLimiter

logger = logging.getLogger(__name__)

# Default singleton instance for auth
login_rate_limiter = InMemoryRateLimiter()


def login_key(username: str, request: Request) -> str:
    """The lockout key for a name on one device: 'ana@192.168.8.40'.

    Wrong PINs count per name *and* address, so a student cannot lock the teacher
    out from another phone. Login and the credential changes share the key, so a
    stolen session cannot double its guesses there. Behind nginx, uvicorn reads
    the client address from X-Forwarded-For.
    """
    return f"{username}@{request.client.host if request.client else '-'}"


def check_rate_limit(
    key: str, limiter: InMemoryRateLimiter = login_rate_limiter
) -> None:
    """
    Raises HTTP 429 Too Many Requests if the key (login: name@address) is locked out.
    """
    if limiter.is_locked_out(key):
        logger.warning("Blocked login attempt for locked out key '%s'.", key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )
