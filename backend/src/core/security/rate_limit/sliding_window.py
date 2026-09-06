import threading
import time
from collections import deque

from .config import (
    DEFAULT_SIGNUP_MAX_EVENTS,
    DEFAULT_SIGNUP_WINDOW_SECONDS,
    get_signup_max_events,
    get_signup_window_seconds,
)

SIGNUP_MAX_EVENTS = DEFAULT_SIGNUP_MAX_EVENTS
SIGNUP_WINDOW_SECONDS = DEFAULT_SIGNUP_WINDOW_SECONDS


class SlidingWindowLimiter:
    """
    Thread-safe global event-window limiter (no per-key state).
    Used to bound account-creation floods on the shared Jetson.
    """

    def __init__(
        self,
        max_events: int | None = None,
        window_seconds: int | None = None,
    ):
        self.max_events = (
            max_events if max_events is not None else get_signup_max_events()
        )
        self.window_seconds = (
            window_seconds
            if window_seconds is not None
            else get_signup_window_seconds()
        )
        self._events: deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = time.time()
        with self._lock:
            while self._events and now - self._events[0] > self.window_seconds:
                self._events.popleft()
            if len(self._events) >= self.max_events:
                return False
            self._events.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


signup_rate_limiter = SlidingWindowLimiter(SIGNUP_MAX_EVENTS, SIGNUP_WINDOW_SECONDS)
