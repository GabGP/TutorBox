"""Tutor turn gate: one turn at a time per login, and a per-minute cap.

A 1.5B model on the classroom Jetson answers in seconds, not milliseconds; a
child tapping "Enviar" repeatedly must not queue several generations.
"""

import threading
import time
from collections import deque
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from fastapi import HTTPException, status

__all__ = ["TurnGate"]


class TurnGate:
    def __init__(
        self,
        turns_per_minute: int,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limit = turns_per_minute
        self._window = window_seconds
        self._clock = clock
        self._busy: set[str] = set()
        self._recent: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    @contextmanager
    def turn(self, key: str) -> Iterator[None]:
        """Holds the login's single turn slot; raises 429 when not allowed."""
        self._enter(key)
        try:
            yield
        finally:
            with self._lock:
                self._busy.discard(key)

    def _enter(self, key: str) -> None:
        now = self._clock()
        with self._lock:
            if key in self._busy:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Espera la respuesta del tutor.",
                )
            recent = self._recent.setdefault(key, deque())
            while recent and now - recent[0] > self._window:
                recent.popleft()
            if len(recent) >= self._limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Vas muy rápido. Espera un momento y vuelve a intentarlo.",
                )
            recent.append(now)
            self._busy.add(key)
