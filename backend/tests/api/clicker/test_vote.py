"""Clicker votes: the hardware transport into the shared session engine."""

import time

from modes.quiz.session.events import get_shared_timers
from modes.quiz.session.timer import RoundTimer
from tests.api.clicker.helpers import (
    CLICKER_ID,
    OTHER_SECRET,
    assign,
    checkin,
    clicker_vote,
    seed_questions,
    start_match,
)
from tests.conftest import auth_headers, get_user_id


def _ready_clicker(staff_db, client, student="student1"):
    """An enrolled clicker assigned to `student`, with round 0 of a match open."""
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    assert checkin(client).status_code == 200
    assign(client, teacher, CLICKER_ID, get_user_id(conn, student))
    session_id = start_match(client, teacher, seed_questions(conn))
    return conn, teacher, session_id, f"{session_id}_r0"


def test_assigned_clicker_vote_is_recorded_as_hardware(staff_db, client):
    conn, _, session_id, round_id = _ready_clicker(staff_db, client)

    response = clicker_vote(client, round_id, "B", response_time_ms=1250.0)

    assert response.status_code == 200
    body = response.json()
    assert (body["round_id"], body["selected_option"]) == (round_id, "B")
    assert body["vote_id"].startswith("v_")
    row = conn.execute(
        "SELECT * FROM quiz_session_votes WHERE id = ?", (body["vote_id"],)
    ).fetchone()
    assert row["session_id"] == session_id
    assert row["student_id"] == get_user_id(conn, "student1")
    assert (row["transport_type"], row["device_id"]) == ("hardware", CLICKER_ID)
    assert (row["is_correct"], row["misconception"]) == (0, "plus_one")
    assert row["response_time_ms"] == 1250.0


def test_second_press_is_final_and_the_lock_is_shared_with_phones(staff_db, client):
    _, _, session_id, round_id = _ready_clicker(staff_db, client)
    phone = auth_headers(client, "student1")

    first = clicker_vote(client, round_id, "C")
    again = clicker_vote(client, round_id, "A")
    from_phone = client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "A"},
        headers=phone,
    )

    assert first.status_code == 200
    assert again.status_code == 409
    assert "already voted" in again.json()["detail"]
    assert from_phone.status_code == 409


def test_student_who_answered_on_a_phone_cannot_vote_again_by_clicker(staff_db, client):
    _, _, session_id, round_id = _ready_clicker(staff_db, client)
    phone = auth_headers(client, "student1")
    phone_vote = client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "D"},
        headers=phone,
    )

    response = clicker_vote(client, round_id, "A")

    assert phone_vote.status_code == 200
    assert response.status_code == 409


def test_unassigned_clicker_cannot_vote(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    checkin(client)
    session_id = start_match(client, teacher, seed_questions(conn))

    response = clicker_vote(client, f"{session_id}_r0")

    assert response.status_code == 403
    assert response.json()["detail"] == "Clicker is not assigned to any student."


def test_unknown_or_impostor_clicker_is_401_and_voting_never_enrolls(staff_db, client):
    conn, teacher, _, round_id = _ready_clicker(staff_db, client)
    client.post("/api/v1/staff/devices", json={"device_id": "9"}, headers=teacher)

    unknown = clicker_vote(client, round_id, device_id="ESP32-FFFFFF")
    impostor = clicker_vote(client, round_id, secret=OTHER_SECRET)
    never_checked_in = clicker_vote(client, round_id, device_id="9")

    assert [r.status_code for r in (unknown, impostor, never_checked_in)] == [
        401,
        401,
        401,
    ]
    exists = conn.execute(
        "SELECT 1 FROM devices WHERE device_id = 'ESP32-FFFFFF'"
    ).fetchone()
    assert exists is None


def test_unknown_round_is_404(staff_db, client):
    _ready_clicker(staff_db, client)

    response = clicker_vote(client, "s_000000000000_r9")

    assert response.status_code == 404


def test_closed_or_timed_out_round_is_409(staff_db, client):
    _, teacher, session_id, round_id = _ready_clicker(staff_db, client)
    expired = RoundTimer(5)
    expired.start(start_time=time.monotonic() - 60)
    get_shared_timers()[round_id] = expired

    timed_out = clicker_vote(client, round_id)
    client.post(f"/api/v1/session/{session_id}/close", headers=teacher)
    closed = clicker_vote(client, round_id)

    assert timed_out.status_code == 409
    assert "expired" in timed_out.json()["detail"]
    assert closed.status_code == 409
    assert "not open" in closed.json()["detail"]


def test_press_for_the_previous_question_never_lands_on_the_next(staff_db, client):
    conn, teacher, session_id, round_0 = _ready_clicker(staff_db, client)
    for step in ("close", "reveal", "next"):
        assert (
            client.post(
                f"/api/v1/session/{session_id}/{step}", headers=teacher
            ).status_code
            == 200
        )

    late = clicker_vote(client, round_0)
    on_time = clicker_vote(client, f"{session_id}_r1")

    assert late.status_code == 409
    assert on_time.status_code == 200
    rounds = [r[0] for r in conn.execute("SELECT round_id FROM quiz_session_votes")]
    assert rounds == [f"{session_id}_r1"]


def test_vote_payload_is_validated(staff_db, client):
    _, _, _, round_id = _ready_clicker(staff_db, client)

    assert clicker_vote(client, round_id, "E").status_code == 422
    assert clicker_vote(client, "bad round!").status_code == 422
    assert clicker_vote(client, round_id, response_time_ms=-1).status_code == 422
