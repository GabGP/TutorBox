"""One value kept for a few seconds, so several open panels share one set of reads."""

import threading
import time
from collections.abc import Callable
from typing import Generic, TypeVar

__all__ = ["TimedCache"]

ValueType = TypeVar("ValueType")


class TimedCache(Generic[ValueType]):
    """Reuses the value built within the last `ttl_seconds`. The lock makes callers share one build."""

    def __init__(
        self, ttl_seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._entry: tuple[float, ValueType] | None = None

    def get(self, build: Callable[[], ValueType]) -> ValueType:
        """The cached value while it is fresh, otherwise a new one from `build`."""
        with self._lock:
            now = self._clock()
            if self._entry is not None and now - self._entry[0] < self._ttl_seconds:
                return self._entry[1]
            value = build()
            self._entry = (self._clock(), value)
            return value

    def invalidate(self) -> None:
        """Forgets the value, so the next `get` builds a fresh one."""
        with self._lock:
            self._entry = None
