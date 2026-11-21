"""Keeps the quiz model in memory while a batch generates, and drops it after an idle spell.

Ollama keeps models for as long as the backend says so (OLLAMA_KEEP_ALIVE=-1 on the
appliance), so something has to unload the quiz model when nothing needs it. A batch
releases it on its own; the countdown covers a teacher who closes the page mid-batch.
"""

import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Protocol

__all__ = ["CountdownTimer", "QuizModelHold"]


class CountdownTimer(Protocol):
    """The part of threading.Timer the hold uses (a fake in tests)."""

    daemon: bool

    def start(self) -> None: ...

    def cancel(self) -> None: ...


TimerFactory = Callable[[float, Callable[[], None]], CountdownTimer]


class QuizModelHold:
    """Counts generations in flight and arms one idle countdown while none runs."""

    def __init__(
        self,
        idle_seconds: float,
        on_idle: Callable[[], object],
        timer_factory: TimerFactory = threading.Timer,
    ) -> None:
        self._idle_seconds = idle_seconds
        self._on_idle = on_idle
        self._timer_factory = timer_factory
        self._lock = threading.Lock()
        self._generations_in_flight = 0
        self._countdown: CountdownTimer | None = None
        self._countdown_token: object | None = None

    def is_held(self) -> bool:
        """True while a generation runs or a countdown is armed (the model is wanted)."""
        with self._lock:
            return self._generations_in_flight > 0 or self._countdown is not None

    def generation_in_flight(self) -> bool:
        """True while a question generation runs (a countdown alone does not count)."""
        with self._lock:
            return self._generations_in_flight > 0

    def arm(self) -> None:
        """Starts (or restarts) the idle countdown."""
        with self._lock:
            self._restart_countdown_locked()

    def disarm(self) -> None:
        """Stops the countdown; the caller unloads the model itself."""
        with self._lock:
            self._cancel_countdown_locked()

    @contextmanager
    def generation(self, ensure_loaded: Callable[[], object]) -> Iterator[None]:
        """Marks one generation in flight: no countdown runs while it does."""
        with self._lock:
            self._generations_in_flight += 1
            self._cancel_countdown_locked()
        try:
            ensure_loaded()
            yield
        finally:
            with self._lock:
                self._generations_in_flight -= 1
                if self._generations_in_flight == 0:
                    self._restart_countdown_locked()

    def _restart_countdown_locked(self) -> None:
        self._cancel_countdown_locked()
        token = object()
        self._countdown_token = token
        countdown = self._timer_factory(self._idle_seconds, lambda: self._expire(token))
        countdown.daemon = True
        self._countdown = countdown
        countdown.start()

    def _cancel_countdown_locked(self) -> None:
        if self._countdown is not None:
            self._countdown.cancel()
        self._countdown = None
        self._countdown_token = None

    def _expire(self, token: object) -> None:
        """Runs when a countdown ends, unless it was replaced, cancelled or overtaken."""
        with self._lock:
            if token is not self._countdown_token or self._generations_in_flight > 0:
                return
            self._countdown = None
            self._countdown_token = None
        self._on_idle()
