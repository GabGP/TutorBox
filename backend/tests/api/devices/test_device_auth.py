"""POST /api/v1/devices/auth: a clicker's secret trades for its student's login session."""

import logging
import sqlite3
import uuid

import pytest
from fastapi.testclient import TestClient

from core.db.device_repository import store_device_secret
from core.security import token_digest
from tests.conftest import auth_headers, get_user_id

AUTH_URL = "/api/v1/devices/auth"
PROFILE_URL = "/api/v1/users/me"
DEVICE_ID = "ESP32_01"
SECRET = "0123456789abcdef0123456789abcdef"
WRONG_SECRET = "fedcba9876543210fedcba9876543210"
UNASSIGNED_DETAIL = "Device is not assigned to any student."


def seed_clicker(
    conn: sqlite3.Connection,
    device_id: str,
    assigned_user_id: int | None,
    *,
    with_secret: bool = True,
) -> None:
    """Registers a clicker, and optionally issues it SECRET."""
    conn.execute(
        "INSERT INTO devices (device_id, assigned_user_id) VALUES (?, ?)",
        (device_id, assigned_user_id),
    )
    if with_secret:
        store_device_secret(conn, device_id, token_digest(SECRET))
    conn.commit()


def post_auth(client: TestClient, device_id: str, secret: str):
    return client.post(AUTH_URL, json={"device_id": device_id, "secret": secret})


def read_profile(client: TestClient, token: str):
    return client.get(PROFILE_URL, headers={"Authorization": f"Bearer {token}"})


def test_right_secret_returns_session_for_the_assigned_student(staff_db, client):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, get_user_id(conn, "student1"))

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 200
    body = response.json()
    assert str(uuid.UUID(body["session_id"])) == body["session_id"]
    assert body["username"] == "student1"
    assert body["device_id"] == DEVICE_ID


def test_issued_token_reads_the_assigned_students_profile(staff_db, client):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, get_user_id(conn, "student1"))
    token = post_auth(client, DEVICE_ID, SECRET).json()["session_id"]

    response = read_profile(client, token)

    assert response.status_code == 200
    assert response.json()["username"] == "student1"


def test_session_row_keeps_digest_student_and_clicker_but_not_token(staff_db, client):
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    seed_clicker(conn, DEVICE_ID, student_id)
    token = post_auth(client, DEVICE_ID, SECRET).json()["session_id"]

    row = conn.execute(
        "SELECT id, user_id, device_id, is_active FROM sessions WHERE device_id = ?",
        (DEVICE_ID,),
    ).fetchone()
    assert row["id"] == token_digest(token)
    assert row["user_id"] == student_id
    assert row["device_id"] == DEVICE_ID
    assert row["is_active"] == 1
    raw_token_rows = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE id = ?", (token,)
    ).fetchone()[0]
    assert raw_token_rows == 0


def test_unknown_device_is_refused_with_401(staff_db, client):
    response = post_auth(client, "NO_SUCH_DEVICE", SECRET)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid device credentials."


def test_wrong_secret_is_refused_with_401(staff_db, client):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, get_user_id(conn, "student1"))

    response = post_auth(client, DEVICE_ID, WRONG_SECRET)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid device credentials."


def test_registered_device_without_a_secret_is_refused_with_401(staff_db, client):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, get_user_id(conn, "student1"), with_secret=False)

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid device credentials."


def test_unknown_wrong_and_unissued_devices_get_identical_responses(staff_db, client):
    _, conn = staff_db
    seed_clicker(conn, "ESP32_WRONG", get_user_id(conn, "student1"))
    seed_clicker(
        conn, "ESP32_UNISSUED", get_user_id(conn, "student2"), with_secret=False
    )

    unknown = post_auth(client, "NO_SUCH_DEVICE", SECRET)
    wrong = post_auth(client, "ESP32_WRONG", WRONG_SECRET)
    unissued = post_auth(client, "ESP32_UNISSUED", SECRET)

    assert unknown.status_code == wrong.status_code == unissued.status_code == 401
    assert unknown.json() == wrong.json() == unissued.json()


def test_right_secret_on_unassigned_device_is_403_and_creates_no_session(
    staff_db, client
):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, None)

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 403
    assert response.json()["detail"] == UNASSIGNED_DETAIL
    session_rows = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE device_id = ?", (DEVICE_ID,)
    ).fetchone()[0]
    assert session_rows == 0


def test_device_whose_student_is_soft_deleted_is_403(staff_db, client):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, get_user_id(conn, "student1"))
    conn.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE username = 'student1'"
    )
    conn.commit()

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 403
    assert response.json()["detail"] == UNASSIGNED_DETAIL


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {"device_id": "clicker/01", "secret": SECRET},
            id="illegal_device_character",
        ),
        pytest.param(
            {"device_id": "d" * 33, "secret": SECRET}, id="device_id_too_long"
        ),
        pytest.param(
            {"device_id": DEVICE_ID, "secret": "0" * 31}, id="secret_too_short"
        ),
        pytest.param(
            {"device_id": DEVICE_ID, "secret": SECRET.upper()}, id="secret_uppercase"
        ),
        pytest.param(
            {"device_id": DEVICE_ID, "secret": "0" * 31 + "g"},
            id="secret_non_hex_letter",
        ),
        pytest.param({"device_id": DEVICE_ID}, id="missing_secret"),
        pytest.param({"secret": SECRET}, id="missing_device_id"),
    ],
)
def test_malformed_request_is_rejected_with_422(staff_db, client, payload):
    response = client.post(AUTH_URL, json=payload)

    assert response.status_code == 422


def test_second_authentication_ends_the_first_token(staff_db, client):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, get_user_id(conn, "student1"))
    first = post_auth(client, DEVICE_ID, SECRET).json()["session_id"]
    second = post_auth(client, DEVICE_ID, SECRET).json()["session_id"]

    assert read_profile(client, first).status_code == 401
    assert read_profile(client, second).status_code == 200


def test_phone_login_of_the_same_student_survives_clicker_authentication(
    staff_db, client
):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, get_user_id(conn, "student1"))
    post_auth(client, DEVICE_ID, SECRET)

    phone_headers = auth_headers(client, "student1")

    response = client.get(PROFILE_URL, headers=phone_headers)
    assert response.status_code == 200


def test_secret_and_tokens_never_reach_the_logs(staff_db, client, caplog):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, get_user_id(conn, "student1"))

    with caplog.at_level(logging.DEBUG):
        token = post_auth(client, DEVICE_ID, SECRET).json()["session_id"]
        post_auth(client, DEVICE_ID, WRONG_SECRET)

    assert f"Device '{DEVICE_ID}' authenticated." in caplog.text
    assert f"Device authentication failed for device '{DEVICE_ID}'." in caplog.text
    for sensitive_value in (
        SECRET,
        WRONG_SECRET,
        token,
        token_digest(SECRET),
        token_digest(token),
    ):
        assert sensitive_value not in caplog.text
