"""A game's first round shows a 3-2-1 on every screen and takes no vote until it ends."""

import pytest

from modes.quiz.session.timer import RoundTimer
from tests.api.session.test_session_public_state import _create
from tests.conftest import auth_headers


@pytest.fixture
def three_second_countdown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QUIZ_START_COUNTDOWN_SECONDS", "3")


@pytest.fixture
def frozen_clock(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Every RoundTimer reads this clock; a test moves time by changing now[0]."""
    now = [1000.0]

    def timer_with_frozen_clock(self: RoundTimer, duration_seconds: int = 30, **_):
        original_init(self, duration_seconds, clock=lambda: now[0])

    original_init = RoundTimer.__init__
    monkeypatch.setattr(RoundTimer, "__init__", timer_with_frozen_clock)
    return now


def _vote(client, session_id: str, student: str):
    return client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "A"},
        headers=auth_headers(client, student),
    )


def test_the_first_round_counts_down_then_takes_votes(
    staff_db, client, three_second_countdown, frozen_clock
):
    _, conn = staff_db
    session_id = _create(client, conn)
    teacher = auth_headers(client, "teacher1")

    started = client.post(f"/api/v1/session/{session_id}/start", headers=teacher)

    first_round = started.json()["current_round"]
    assert first_round["starts_in"] == 3.0
    assert first_round["time_remaining"] == first_round["duration_seconds"]
    # Every screen reads the public state: the countdown is there too.
    public = client.get("/api/v1/session/current").json()["current_round"]
    assert public["starts_in"] == 3.0

    early = _vote(client, session_id, "student1")
    assert early.status_code == 409
    assert "countdown" in early.json()["detail"]

    frozen_clock[0] += 3.0
    assert client.get("/api/v1/session/current").json()["current_round"][
        "starts_in"
    ] == pytest.approx(0.0)
    assert _vote(client, session_id, "student1").status_code == 200


def test_later_rounds_open_without_a_countdown(
    staff_db, client, three_second_countdown, frozen_clock
):
    _, conn = staff_db
    session_id = _create(client, conn)
    teacher = auth_headers(client, "teacher1")
    client.post(f"/api/v1/session/{session_id}/start", headers=teacher)
    frozen_clock[0] += 3.0
    client.post(f"/api/v1/session/{session_id}/close", headers=teacher)
    client.post(f"/api/v1/session/{session_id}/reveal", headers=teacher)

    second = client.post(f"/api/v1/session/{session_id}/next", headers=teacher)

    assert second.json()["current_round"]["round_index"] == 1
    assert second.json()["current_round"]["starts_in"] == 0.0


def test_no_countdown_when_it_is_turned_off(staff_db, client):
    _, conn = staff_db
    session_id = _create(client, conn)
    teacher = auth_headers(client, "teacher1")

    started = client.post(f"/api/v1/session/{session_id}/start", headers=teacher)

    assert started.json()["current_round"]["starts_in"] == 0.0
    assert _vote(client, session_id, "student1").status_code == 200
