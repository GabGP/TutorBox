"""Monotonic countdown timer for question round voting windows."""

import time
from collections.abc import Callable


class RoundTimer:
    """Tracks elapsed and remaining duration using a monotonic clock."""

    def __init__(
        self,
        duration_seconds: int = 30,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.duration_seconds: float = float(max(1, duration_seconds))
        self._clock = clock
        self._started_at_monotonic: float | None = None
        self._is_stopped: bool = False

    def start(self, *, start_time: float | None = None) -> None:
        """Starts the round timer."""
        self._started_at_monotonic = (
            start_time if start_time is not None else self._clock()
        )
        self._is_stopped = False

    def stop(self) -> None:
        """Stops the round timer."""
        self._is_stopped = True

    def is_running(self, *, current_time: float | None = None) -> bool:
        """Indicates whether the timer is currently active and not expired."""
        if self._started_at_monotonic is None or self._is_stopped:
            return False
        return not self.is_expired(current_time=current_time)

    def elapsed_seconds(self, *, current_time: float | None = None) -> float:
        """Returns elapsed seconds since start."""
        if self._started_at_monotonic is None:
            return 0.0
        now = current_time if current_time is not None else self._clock()
        return max(0.0, now - self._started_at_monotonic)

    def remaining_seconds(self, *, current_time: float | None = None) -> float:
        """Returns remaining seconds, clamped to 0.0."""
        if self._started_at_monotonic is None or self._is_stopped:
            return 0.0
        remaining = self.duration_seconds - self.elapsed_seconds(
            current_time=current_time
        )
        return max(0.0, remaining)

    def is_expired(self, *, current_time: float | None = None) -> bool:
        """Checks whether the voting duration has elapsed."""
        if self._started_at_monotonic is None:
            return False
        if self._is_stopped:
            return True
        return self.remaining_seconds(current_time=current_time) <= 0.0
