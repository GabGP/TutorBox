import logging
import time
from collections import defaultdict

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes


class InMemoryRateLimiter:
    """
    Lightweight in-memory rate limiter for tracking failed authentication attempts.
    Locks out a username after MAX_ATTEMPTS consecutive failures for LOCKOUT_DURATION_SECONDS.
    """

    def __init__(
        self,
        max_attempts: int = MAX_ATTEMPTS,
        lockout_seconds: int = LOCKOUT_DURATION_SECONDS,
    ):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._failed_attempts: dict[str, int] = defaultdict(int)
        self._lockout_until: dict[str, float] = {}

    def is_locked_out(self, key: str) -> bool:
        """
        Checks if the given key (username) is currently locked out.
        Automatically cleans up expired lockouts.
        """
        now = time.time()
        lockout_time = self._lockout_until.get(key)

        if lockout_time is not None:
            if now < lockout_time:
                return True
            # Lockout expired, reset counter and lockout
            del self._lockout_until[key]
            self._failed_attempts[key] = 0

        return False

    def record_failure(self, key: str) -> bool:
        """
        Records a failed attempt. If failures reach max_attempts, locks out the key.
        Returns True if the key is now locked out.
        """
        self._failed_attempts[key] += 1
        if self._failed_attempts[key] >= self.max_attempts:
            self._lockout_until[key] = time.time() + self.lockout_seconds
            logger.warning(
                "User '%s' exceeded max failed login attempts (%d). Locked out for %d seconds.",
                key,
                self.max_attempts,
                self.lockout_seconds,
            )
            return True
        return False

    def record_success(self, key: str) -> None:
        """
        Resets failed attempts and lockout status for a key upon successful authentication.
        """
        self._failed_attempts.pop(key, None)
        self._lockout_until.pop(key, None)

    def clear(self) -> None:
        """
        Clears all rate limiting state.
        """
        self._failed_attempts.clear()
        self._lockout_until.clear()


# Default singleton instance for auth
login_rate_limiter = InMemoryRateLimiter()


def check_rate_limit(
    username: str, limiter: InMemoryRateLimiter = login_rate_limiter
) -> None:
    """
    Raises HTTP 429 Too Many Requests if the username is currently locked out.
    """
    if limiter.is_locked_out(username):
        logger.warning("Blocked login attempt for locked out user '%s'.", username)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )
