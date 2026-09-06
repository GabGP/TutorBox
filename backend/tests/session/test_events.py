"""Unit tests for session event dispatcher and shared state isolation."""

from session.events import (
    emit_event,
    get_shared_listeners,
    get_shared_timers,
    reset_shared_session_state,
)
from session.timer import RoundTimer


def test_shared_state_accessors():
    """Accessors return shared dictionary and list structures."""
    timers = get_shared_timers()
    listeners = get_shared_listeners()
    assert isinstance(timers, dict)
    assert isinstance(listeners, list)


def test_emit_event_dispatches_to_all_listeners():
    """emit_event broadcasts event name and payload to all registered listeners."""
    dispatched = []

    def listener_a(event_name: str, payload: dict) -> None:
        dispatched.append(("A", event_name, payload))

    def listener_b(event_name: str, payload: dict) -> None:
        dispatched.append(("B", event_name, payload))

    emit_event([listener_a, listener_b], "test_event", {"key": "val"})
    assert len(dispatched) == 2
    assert dispatched[0] == ("A", "test_event", {"key": "val"})
    assert dispatched[1] == ("B", "test_event", {"key": "val"})


def test_reset_shared_session_state():
    """reset_shared_session_state clears shared timers and listeners cleanly."""
    timers = get_shared_timers()
    listeners = get_shared_listeners()

    timer = RoundTimer(duration_seconds=10)
    timers["round_test_1"] = timer
    listeners.append(lambda name, payload: None)

    assert len(timers) > 0
    assert len(listeners) > 0

    reset_shared_session_state()

    assert len(timers) == 0
    assert len(listeners) == 0
