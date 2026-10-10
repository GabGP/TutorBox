"""A clicker's token can vote and nothing else: every other endpoint refuses it."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from core.db.device_repository import store_device_secret
from core.security import token_digest
from tests.api.clicker_support import clicker_token_is_live
from tests.conftest import auth_headers, get_user_id

AUTH_URL = "/api/v1/devices/auth"
GAME_EVENTS_URL = "/api/v1/games/events"
DEVICE_ID = "ESP32_01"
SECRET = "0123456789abcdef0123456789abcdef"
CLICKER_SCOPE_DETAIL = "Clicker sessions can only vote."
GAME_EVENT = {
    "client_event_id": "evt-0000000000000001",
    "grade": "primero",
    "lesson_id": "sumar-jocotes",
    "round_index": 0,
    "attempt": 1,
    "is_correct": False,
    "answer": "4",
    "expected": "5",
    "occurred_at": "2026-10-09T15:04:05Z",
    "app_version": "1",
}


def clicker_headers(
    client: TestClient, conn: sqlite3.Connection, student_username: str
) -> dict[str, str]:
    """Registers a clicker for the student and logs it in at the real endpoint."""
    conn.execute(
        "INSERT INTO devices (device_id, assigned_user_id) VALUES (?, ?)",
        (DEVICE_ID, get_user_id(conn, student_username)),
    )
    store_device_secret(conn, DEVICE_ID, token_digest(SECRET))
    conn.commit()
    response = client.post(AUTH_URL, json={"device_id": DEVICE_ID, "secret": SECRET})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['session_id']}"}


@pytest.mark.parametrize(
    ("method", "url", "body"),
    [
        pytest.param("GET", "/api/v1/users/me", None, id="read_profile"),
        pytest.param(
            "PATCH",
            "/api/v1/users/me/pin",
            {"current_pin": "1234", "new_pin": "5678"},
            id="change_pin",
        ),
        pytest.param(
            "PATCH",
            "/api/v1/users/me/username",
            {"current_pin": "1234", "new_username": "renamed_student"},
            id="change_username",
        ),
        pytest.param("POST", "/api/v1/auth/logout", None, id="logout"),
        pytest.param(
            "POST", "/api/v1/tutor/message", {"message": "hola"}, id="tutor_message"
        ),
        pytest.param("POST", "/api/v1/tutor/ping", None, id="tutor_ping"),
        pytest.param("POST", "/api/v1/tutor/reset", None, id="tutor_reset"),
        pytest.param("GET", "/api/v1/staff/devices", None, id="staff_device_list"),
    ],
)
def test_a_clicker_token_is_refused_outside_voting(staff_db, client, method, url, body):
    _, conn = staff_db
    clicker = clicker_headers(client, conn, "student1")

    response = client.request(method, url, json=body, headers=clicker)

    assert response.status_code == 403
    assert response.json()["detail"] == CLICKER_SCOPE_DETAIL


def test_a_phone_login_of_the_same_student_is_still_accepted(staff_db, client):
    _, conn = staff_db
    clicker_headers(client, conn, "student1")
    phone = auth_headers(client, "student1")

    response = client.get("/api/v1/users/me", headers=phone)

    assert response.status_code == 200
    assert response.json()["username"] == "student1"


def test_a_refused_logout_leaves_the_clicker_able_to_vote(staff_db, client):
    _, conn = staff_db
    clicker = clicker_headers(client, conn, "student1")

    refused = client.post("/api/v1/auth/logout", headers=clicker)

    assert refused.status_code == 403
    assert clicker_token_is_live(client, clicker)


def test_a_refused_pin_change_leaves_the_students_pin_unchanged(staff_db, client):
    _, conn = staff_db
    clicker = clicker_headers(client, conn, "student1")

    client.patch(
        "/api/v1/users/me/pin",
        json={"current_pin": "1234", "new_pin": "5678"},
        headers=clicker,
    )

    assert auth_headers(client, "student1", pin="1234")


def test_game_events_sent_with_a_clicker_token_carry_no_student(staff_db, client):
    _, conn = staff_db
    clicker = clicker_headers(client, conn, "student1")

    response = client.post(
        GAME_EVENTS_URL,
        json={"install_id": "install-000000000001", "events": [GAME_EVENT]},
        headers=clicker,
    )

    assert response.status_code == 200
    assert response.json()["accepted"] == 1
    row = conn.execute("SELECT student_id FROM game_events").fetchone()
    assert row["student_id"] is None
