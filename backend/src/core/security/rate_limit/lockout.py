import logging
import threading
import time

from fastapi import HTTPException, status

from .config import (
    DEFAULT_LOCKOUT_DURATION_SECONDS,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_MAX_TRACKED_KEYS,
    get_auth_lockout_seconds,
    get_auth_max_attempts,
    get_auth_max_tracked_keys,
)

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = DEFAULT_MAX_ATTEMPTS
LOCKOUT_DURATION_SECONDS = DEFAULT_LOCKOUT_DURATION_SECONDS
MAX_TRACKED_KEYS = DEFAULT_MAX_TRACKED_KEYS


class InMemoryRateLimiter:
    """Lightweight in-memory rate limiter for failed authentication attempts."""

    def __init__(
        self,
        max_attempts: int | None = None,
        lockout_seconds: int | None = None,
        max_tracked_keys: int | None = None,
    ):
        self.max_attempts = (
            max_attempts if max_attempts is not None else get_auth_max_attempts()
        )
        self.lockout_seconds = (
            lockout_seconds
            if lockout_seconds is not None
            else get_auth_lockout_seconds()
        )
        self.max_tracked_keys = (
            max_tracked_keys
            if max_tracked_keys is not None
            else get_auth_max_tracked_keys()
        )
        self._failed_attempts: dict[str, int] = {}
        self._lockout_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def _evict_stale(self) -> None:
        """
        Removes expired lockouts together with their failure counters.
        Caller must hold self._lock.
        """
        now = time.time()
        for key in list(self._lockout_until):
            if now >= self._lockout_until[key]:
                del self._lockout_until[key]
                self._failed_attempts.pop(key, None)

    def _enforce_cap(self) -> None:
        """
        Hard-caps tracked keys. Locked-out keys are never evicted; the oldest
        non-locked-out entries (insertion order) are dropped first.
        Caller must hold self._lock.
        """
        excess = len(self._failed_attempts) - self.max_tracked_keys
        for key in list(self._failed_attempts):
            if excess <= 0:
                break
            if key not in self._lockout_until:
                del self._failed_attempts[key]
                excess -= 1

    def is_locked_out(self, key: str) -> bool:
        """
        Checks if the given key (username) is currently locked out.
        Automatically cleans up expired lockouts.
        """
        with self._lock:
            now = time.time()
            lockout_time = self._lockout_until.get(key)

            if lockout_time is not None:
                if now < lockout_time:
                    return True
                # Lockout expired, reset counter and lockout
                del self._lockout_until[key]
                self._failed_attempts.pop(key, None)

            return False

    def record_failure(self, key: str) -> bool:
        """
        Records a failed attempt. If failures reach max_attempts, locks out
        the key. Returns True if the key is now locked out.
        """
        with self._lock:
            self._evict_stale()
            self._failed_attempts[key] = self._failed_attempts.get(key, 0) + 1
            locked_now = self._failed_attempts[key] >= self.max_attempts
            if locked_now:
                self._lockout_until[key] = time.time() + self.lockout_seconds
                logger.warning(
                    "User '%s' exceeded max failed login attempts (%d). Locked out for %d seconds.",
                    key,
                    self.max_attempts,
                    self.lockout_seconds,
                )
            # Enforce the cap last so freshly locked-out keys are never evicted.
            self._enforce_cap()
            return locked_now

    def record_success(self, key: str) -> None:
        """
        Resets failed attempts and lockout status for a key upon successful
        authentication.
        """
        with self._lock:
            self._failed_attempts.pop(key, None)
            self._lockout_until.pop(key, None)

    def clear(self) -> None:
        """
        Clears all rate limiting state.
        """
        with self._lock:
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
