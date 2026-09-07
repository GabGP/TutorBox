"""Event dispatcher and shared in-memory state for real-time quiz sessions."""

from collections.abc import Callable
from typing import Any

from modes.quiz.session.timer import RoundTimer

EventListener = Callable[[str, dict[str, Any]], None]

_SHARED_TIMERS: dict[str, RoundTimer] = {}
_SHARED_LISTENERS: list[EventListener] = []


def get_shared_timers() -> dict[str, RoundTimer]:
    """Returns reference to shared in-memory round timers."""
    return _SHARED_TIMERS


def get_shared_listeners() -> list[EventListener]:
    """Returns reference to shared in-memory event listeners."""
    return _SHARED_LISTENERS


def emit_event(
    listeners: list[EventListener], event_name: str, payload: dict[str, Any]
) -> None:
    """Dispatches an event to all registered listeners."""
    for listener in listeners:
        listener(event_name, payload)


def reset_shared_session_state() -> None:
    """Resets in-memory timers and listeners for clean test isolation."""
    _SHARED_TIMERS.clear()
    _SHARED_LISTENERS.clear()
