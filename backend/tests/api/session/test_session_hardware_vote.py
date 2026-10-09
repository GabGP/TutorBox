"""Clicker votes on the shared vote endpoint: the server labels every vote from the session."""

import sqlite3
import uuid

from fastapi.testclient import TestClient

from core.db.device_repository import create_device_session, revoke_device_sessions
from core.db.question_repository import create_question
from core.security.auth_session import token_digest
from modes.quiz.contracts.models import DistractorDetail, QuizQuestionCreate
from tests.conftest import auth_headers, get_user_id

CLICKER_ID = "ESP32-A4CF12"


def _seed_question(conn: sqlite3.Connection) -> str:
    question_id = create_question(
        conn,
        QuizQuestionCreate(
            topic="arithmetic",
            subconcept="addition",
            question_text="2 + 3?",
            options={"A": "5", "B": "6", "C": "4", "D": "1"},
            correct_option="A",
            distractors={
                "B": DistractorDetail(
                    misconception="plus_one", explanation="Sumaste 1 de mas."
                ),
                "C": DistractorDetail(
                    misconception="minus_one", explanation="Sumaste 1 de menos."
                ),
                "D": DistractorDetail(
                    misconception="subtracted", explanation="Restaste."
                ),
            },
        ),
    )
    conn.commit()
    return question_id


def _open_first_round(client: TestClient, conn: sqlite3.Connection) -> str:
    """Creates a one-question match as teacher1 and opens its first round."""
    teacher = auth_headers(client, "teacher1")
    created = client.post(
        "/api/v1/session",
        json={
            "title": "Clicker match",
            "topic": "arithmetic",
            "question_ids": [_seed_question(conn)],
        },
        headers=teacher,
    )
    assert created.status_code == 201
    session_id = created.json()["id"]
    started = client.post(f"/api/v1/session/{session_id}/start", headers=teacher)
    assert started.status_code == 200
    return session_id


def _assign_clicker(conn: sqlite3.Connection, student_username: str) -> dict[str, str]:
    """Assigns the clicker to a student and issues it the login the clicker holds."""
    student_id = get_user_id(conn, student_username)
    conn.execute(
        "INSERT INTO devices (device_id, assigned_user_id) VALUES (?, ?)",
        (CLICKER_ID, student_id),
    )
    token = str(uuid.uuid4())
    create_device_session(conn, token_digest(token), student_id, CLICKER_ID)
    conn.commit()
    return {"Authorization": f"Bearer {token}"}


def _vote(
    client: TestClient,
    session_id: str,
    headers: dict[str, str],
    selected_option: str,
    **extra_fields: str,
):
    return client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": selected_option, **extra_fields},
        headers=headers,
    )


def _stored_votes(conn: sqlite3.Connection, session_id: str) -> list[tuple]:
    """(transport_type, device_id, student_id) of every vote, ordered by student."""
    rows = conn.execute(
        "SELECT transport_type, device_id, student_id FROM quiz_session_votes "
        "WHERE session_id = ? ORDER BY student_id",
        (session_id,),
    ).fetchall()
    return [tuple(row) for row in rows]


def _first_round_id(conn: sqlite3.Connection, session_id: str) -> str:
    row = conn.execute(
        "SELECT id FROM quiz_session_rounds WHERE session_id = ? AND round_index = 0",
        (session_id,),
    ).fetchone()
    return row["id"]


def _votes_in_round_by(conn: sqlite3.Connection, round_id: str, student_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM quiz_session_votes WHERE round_id = ? AND student_id = ?",
        (round_id, student_id),
    ).fetchone()
    return row[0]


def test_a_clicker_vote_is_stored_as_hardware_with_its_device(staff_db, client):
    _, conn = staff_db
    session_id = _open_first_round(client, conn)
    clicker = _assign_clicker(conn, "student1")

    response = _vote(client, session_id, clicker, "A")

    assert response.status_code == 200
    student1_id = get_user_id(conn, "student1")
    assert _stored_votes(conn, session_id) == [("hardware", CLICKER_ID, student1_id)]


def test_a_phone_vote_is_stored_as_web_with_no_device(staff_db, client):
    _, conn = staff_db
    session_id = _open_first_round(client, conn)
    phone = auth_headers(client, "student1")

    response = _vote(client, session_id, phone, "A")

    assert response.status_code == 200
    student1_id = get_user_id(conn, "student1")
    assert _stored_votes(conn, session_id) == [("web", None, student1_id)]


def test_a_phone_body_claiming_hardware_is_stored_as_web(staff_db, client):
    _, conn = staff_db
    session_id = _open_first_round(client, conn)
    phone = auth_headers(client, "student1")

    response = _vote(
        client,
        session_id,
        phone,
        "A",
        transport_type="hardware",
        device_id=CLICKER_ID,
    )

    assert response.status_code == 200
    student1_id = get_user_id(conn, "student1")
    assert _stored_votes(conn, session_id) == [("web", None, student1_id)]


def test_a_clicker_body_claiming_web_is_stored_as_hardware(staff_db, client):
    _, conn = staff_db
    session_id = _open_first_round(client, conn)
    clicker = _assign_clicker(conn, "student1")

    response = _vote(
        client,
        session_id,
        clicker,
        "A",
        transport_type="web",
        device_id="OTHER",
    )

    assert response.status_code == 200
    student1_id = get_user_id(conn, "student1")
    assert _stored_votes(conn, session_id) == [("hardware", CLICKER_ID, student1_id)]


def test_a_clicker_second_press_in_the_same_round_is_rejected(staff_db, client):
    _, conn = staff_db
    session_id = _open_first_round(client, conn)
    clicker = _assign_clicker(conn, "student1")
    assert _vote(client, session_id, clicker, "A").status_code == 200

    second = _vote(client, session_id, clicker, "B")

    assert second.status_code == 409
    student1_id = get_user_id(conn, "student1")
    round_id = _first_round_id(conn, session_id)
    assert _votes_in_round_by(conn, round_id, student1_id) == 1


def test_the_first_press_locks_across_transports(staff_db, client):
    _, conn = staff_db
    session_id = _open_first_round(client, conn)
    clicker = _assign_clicker(conn, "student1")
    phone = auth_headers(client, "student1")
    assert _vote(client, session_id, clicker, "A").status_code == 200

    second = _vote(client, session_id, phone, "B")

    assert second.status_code == 409
    student1_id = get_user_id(conn, "student1")
    assert _stored_votes(conn, session_id) == [("hardware", CLICKER_ID, student1_id)]


def test_a_revoked_clicker_session_cannot_vote(staff_db, client):
    _, conn = staff_db
    session_id = _open_first_round(client, conn)
    clicker = _assign_clicker(conn, "student1")
    revoke_device_sessions(conn, CLICKER_ID)
    conn.commit()

    response = _vote(client, session_id, clicker, "A")

    assert response.status_code == 401
    assert _stored_votes(conn, session_id) == []


def test_a_clicker_vote_counts_in_the_reveal_like_a_web_vote(staff_db, client):
    _, conn = staff_db
    session_id = _open_first_round(client, conn)
    clicker = _assign_clicker(conn, "student1")
    phone = auth_headers(client, "student2")
    assert _vote(client, session_id, clicker, "A").status_code == 200
    assert _vote(client, session_id, phone, "B").status_code == 200

    teacher = auth_headers(client, "teacher1")
    reveal = client.post(f"/api/v1/session/{session_id}/reveal", headers=teacher)

    assert reveal.status_code == 200
    assert reveal.json()["tally"]["total_votes"] == 2
