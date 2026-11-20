"""Tests for POST /api/v1/session/{id}/abandon: the teacher cancels a match."""

from modes.quiz.session.events import get_shared_timers
from tests.api.session.test_session_errors import _seed_question
from tests.conftest import auth_headers


def _create_match(client, conn, teacher_headers, rounds: int = 2) -> str:
    question_id = _seed_question(conn)
    created = client.post(
        "/api/v1/session",
        json={
            "title": "Cancelar",
            "topic": "arithmetic",
            "question_ids": [question_id] * rounds,
        },
        headers=teacher_headers,
    )
    return created.json()["id"]


def test_cancelling_a_lobby_takes_it_off_current(staff_db, client):
    """A cancelled lobby is no longer offered to students and the screen."""
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    session_id = _create_match(client, conn, teacher)
    assert client.get("/api/v1/session/current").json()["id"] == session_id

    response = client.post(f"/api/v1/session/{session_id}/abandon", headers=teacher)

    assert response.status_code == 200
    assert response.json()["status"] == "abandoned"
    assert client.get("/api/v1/session/current").status_code == 404
    row = conn.execute(
        "SELECT status, ended_at FROM quiz_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    assert row["status"] == "abandoned"
    assert row["ended_at"] is not None


def test_cancelling_mid_round_stops_the_votes(staff_db, client):
    """The open round closes, so a press after the cancel is refused."""
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    student = auth_headers(client, "student1")
    session_id = _create_match(client, conn, teacher)
    client.post(f"/api/v1/session/{session_id}/start", headers=teacher)
    round_id = f"{session_id}_r0"
    assert round_id in get_shared_timers()

    response = client.post(f"/api/v1/session/{session_id}/abandon", headers=teacher)

    assert response.status_code == 200
    assert response.json()["current_round"]["status"] == "closed"
    vote = client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "A"},
        headers=student,
    )
    assert vote.status_code == 409
    timer = get_shared_timers().get(round_id)
    assert timer is None or not timer.is_running()


def test_cancelling_on_the_result_screen_keeps_the_round_as_it_was(staff_db, client):
    """Between questions nothing is open; the match still ends."""
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    session_id = _create_match(client, conn, teacher)
    client.post(f"/api/v1/session/{session_id}/start", headers=teacher)
    client.post(f"/api/v1/session/{session_id}/close", headers=teacher)
    client.post(f"/api/v1/session/{session_id}/reveal", headers=teacher)

    response = client.post(f"/api/v1/session/{session_id}/abandon", headers=teacher)

    assert response.status_code == 200
    assert response.json()["status"] == "abandoned"
    assert response.json()["current_round"]["status"] == "revealed"
    next_round = client.post(f"/api/v1/session/{session_id}/next", headers=teacher)
    assert next_round.status_code == 409


def test_an_ended_match_cannot_be_cancelled(staff_db, client):
    """Cancelling twice, or after the last question, is a 409."""
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    cancelled = _create_match(client, conn, teacher)
    client.post(f"/api/v1/session/{cancelled}/abandon", headers=teacher)
    assert (
        client.post(f"/api/v1/session/{cancelled}/abandon", headers=teacher).status_code
        == 409
    )

    finished = _create_match(client, conn, teacher, rounds=1)
    for step in ("start", "close", "reveal", "next"):
        client.post(f"/api/v1/session/{finished}/{step}", headers=teacher)
    assert (
        client.post(f"/api/v1/session/{finished}/abandon", headers=teacher).status_code
        == 409
    )


def test_only_staff_can_cancel_and_the_match_must_exist(staff_db, client):
    """Students get 403; an unknown id is a 404."""
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    student = auth_headers(client, "student1")
    session_id = _create_match(client, conn, teacher)

    assert (
        client.post(
            f"/api/v1/session/{session_id}/abandon", headers=student
        ).status_code
        == 403
    )
    assert (
        client.post("/api/v1/session/missing_id/abandon", headers=teacher).status_code
        == 404
    )
