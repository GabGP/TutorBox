"""Classroom mode switch (src/api/mode.py): public read, staff-only write."""

from src.core.db.database import get_db
from tests.api.session.test_session_endpoints import _seed_quiz_questions
from tests.conftest import auth_headers, get_user_id


def _start_quiz(client, conn, headers) -> str:
    payload = {
        "title": "Clase",
        "topic": "arithmetic",
        "question_ids": _seed_quiz_questions(conn),
    }
    session_id = client.post("/api/v1/session", json=payload, headers=headers).json()[
        "id"
    ]
    resp = client.post(f"/api/v1/session/{session_id}/start", headers=headers)
    assert resp.status_code == 200
    return session_id


def test_mode_defaults_to_quiz_and_is_public(staff_db, client):
    resp = client.get("/api/v1/mode")  # no auth header on purpose

    assert resp.status_code == 200
    assert resp.json() == {"mode": "quiz"}


def test_teacher_switches_mode_and_everyone_sees_it(staff_db, client):
    headers = auth_headers(client, "teacher1")

    resp = client.put("/api/v1/mode", json={"mode": "tutor"}, headers=headers)

    assert resp.status_code == 200
    assert resp.json() == {"mode": "tutor"}
    assert client.get("/api/v1/mode").json() == {"mode": "tutor"}


def test_mode_change_persists_and_is_audited(staff_db, client):
    _, conn = staff_db
    headers = auth_headers(client, "admin1")

    client.put("/api/v1/mode", json={"mode": "apps"}, headers=headers)

    with get_db() as fresh:  # a new connection, as after a reboot
        row = fresh.execute(
            "SELECT mode, updated_by FROM appliance_state WHERE id = 1"
        ).fetchone()
        audit = fresh.execute(
            "SELECT actor_user_id FROM audit_logs WHERE action = 'mode_changed'"
        ).fetchall()
    admin_id = get_user_id(conn, "admin1")
    assert (row["mode"], row["updated_by"]) == ("apps", admin_id)
    assert [a["actor_user_id"] for a in audit] == [admin_id]


def test_student_cannot_switch_mode(staff_db, client):
    headers = auth_headers(client, "student2")

    resp = client.put("/api/v1/mode", json={"mode": "tutor"}, headers=headers)

    assert resp.status_code == 403
    assert client.get("/api/v1/mode").json() == {"mode": "quiz"}


def test_anonymous_cannot_switch_mode(staff_db, client):
    resp = client.put("/api/v1/mode", json={"mode": "tutor"})

    assert resp.status_code == 401


def test_unknown_mode_is_rejected(staff_db, client):
    headers = auth_headers(client, "teacher1")

    resp = client.put("/api/v1/mode", json={"mode": "games"}, headers=headers)

    assert resp.status_code == 422


def test_cannot_leave_quiz_while_a_game_is_running(staff_db, client):
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    _start_quiz(client, conn, headers)

    resp = client.put("/api/v1/mode", json={"mode": "tutor"}, headers=headers)

    assert resp.status_code == 409
    assert resp.json()["detail"] == "Termina el juego antes de cambiar de modo."
    assert client.get("/api/v1/mode").json() == {"mode": "quiz"}


def test_reselecting_quiz_during_a_game_is_allowed(staff_db, client):
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    _start_quiz(client, conn, headers)

    resp = client.put("/api/v1/mode", json={"mode": "quiz"}, headers=headers)

    assert resp.status_code == 200


def test_lobby_session_does_not_block_mode_change(staff_db, client):
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    payload = {
        "title": "Clase",
        "topic": "arithmetic",
        "question_ids": _seed_quiz_questions(conn),
    }
    client.post("/api/v1/session", json=payload, headers=headers)

    resp = client.put("/api/v1/mode", json={"mode": "apps"}, headers=headers)

    assert resp.status_code == 200
