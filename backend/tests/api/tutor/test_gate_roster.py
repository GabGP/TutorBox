"""Tutor turn gate and teacher roster, with a controlled clock."""

import pytest
from fastapi import HTTPException

from api.tutor.gate import TurnGate
from api.tutor.roster import TutorRoster


def test_one_turn_at_a_time_per_login():
    gate = TurnGate(turns_per_minute=10)

    with gate.turn("a"):
        with pytest.raises(HTTPException) as busy, gate.turn("a"):
            pass
        assert busy.value.status_code == 429
        assert busy.value.detail == "Espera la respuesta del tutor."
        with gate.turn("b"):  # other logins are not blocked
            pass
    with gate.turn("a"):  # released after the turn
        pass


def test_turns_per_minute_slide_with_the_window():
    ticks = iter([0.0, 1.0, 2.0, 61.5])
    gate = TurnGate(turns_per_minute=2, window_seconds=60, clock=lambda: next(ticks))

    for _ in range(2):
        with gate.turn("a"):
            pass
    with pytest.raises(HTTPException), gate.turn("a"):
        pass
    with gate.turn("a"):  # the first two turns left the window
        pass


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_roster_tracks_work_and_connection():
    clock = _Clock()
    roster = TutorRoster(online_seconds=45, forget_seconds=1800, clock=clock)

    roster.seen(1, "ana")
    roster.record(1, "ana", "23 + 45", 0, solved=False)
    roster.record(1, "ana", None, 0, solved=False)  # "gracias": still on 23 + 45
    roster.record(1, "ana", "23 + 45", 2, solved=False)
    roster.record(2, "beto", "7 × 8", 1, solved=False)
    clock.now += 100
    roster.record(1, "ana", "23 + 45", 2, solved=True)

    assert roster.snapshot() == [
        {
            "username": "ana",
            "online": True,
            "seconds_ago": 0,
            "turns": 4,
            "solved": 1,
            "problem": None,
            "hint_level": 0,
        },
        {
            "username": "beto",
            "online": False,
            "seconds_ago": 100,
            "turns": 1,
            "solved": 0,
            "problem": "7 × 8",
            "hint_level": 1,
        },
    ]


def test_roster_clears_on_reset_and_forgets_idle_students():
    clock = _Clock()
    roster = TutorRoster(clock=clock)
    roster.record(1, "ana", "23 + 45", 3, solved=False)

    roster.cleared(1, "ana")
    assert roster.snapshot()[0]["problem"] is None

    clock.now += 1801
    assert roster.snapshot() == []
