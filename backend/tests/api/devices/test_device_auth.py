"""POST /api/v1/devices/auth: a clicker's secret trades for its student's login session."""

import logging
import sqlite3
import uuid

import pytest
from fastapi.testclient import TestClient

from core.security import token_digest
from tests.api.clicker_support import clicker_token_is_live
from tests.api.devices.test_device_enrollment import fill_fleet_to_cap
from tests.conftest import auth_headers, get_user_id

AUTH_URL = "/api/v1/devices/auth"
PROFILE_URL = "/api/v1/users/me"
DEVICE_ID = "ESP32_01"
SECRET = "0123456789abcdef0123456789abcdef"
WRONG_SECRET = "fedcba9876543210fedcba9876543210"
UNASSIGNED_DETAIL = "Device is not assigned to any student."


def post_auth(client: TestClient, device_id: str, secret: str):
    return client.post(AUTH_URL, json={"device_id": device_id, "secret": secret})


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def add_clicker_by_hand(
    conn: sqlite3.Connection, device_id: str, assigned_user_id: int | None
) -> None:
    """Adds a clicker the way a teacher does on the staff screen: a row with no secret."""
    conn.execute(
        "INSERT INTO devices (device_id, assigned_user_id) VALUES (?, ?)",
        (device_id, assigned_user_id),
    )
    conn.commit()


def seed_enrolled_clicker(
    client: TestClient,
    conn: sqlite3.Connection,
    device_id: str,
    assigned_user_id: int | None,
) -> None:
    """Has an unknown clicker make its first contact with SECRET, then assigns it.

    The first contact enrolls SECRET and is refused as unassigned, which writes no
    session, so a test that calls this starts with no session of the clicker.
    """
    first_contact = post_auth(client, device_id, SECRET)
    assert first_contact.status_code == 403, first_contact.text
    conn.execute(
        "UPDATE devices SET assigned_user_id = ? WHERE device_id = ?",
        (assigned_user_id, device_id),
    )
    conn.commit()


def test_right_secret_returns_session_for_the_assigned_student(staff_db, client):
    _, conn = staff_db
    seed_enrolled_clicker(client, conn, DEVICE_ID, get_user_id(conn, "student1"))

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 200
    body = response.json()
    assert str(uuid.UUID(body["session_id"])) == body["session_id"]
    assert body["username"] == "student1"
    assert body["device_id"] == DEVICE_ID


def test_issued_token_is_accepted_by_the_vote_endpoint(staff_db, client):
    _, conn = staff_db
    seed_enrolled_clicker(client, conn, DEVICE_ID, get_user_id(conn, "student1"))
    token = post_auth(client, DEVICE_ID, SECRET).json()["session_id"]

    assert clicker_token_is_live(client, bearer(token))


def test_session_row_keeps_digest_student_and_clicker_but_not_token(staff_db, client):
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    seed_enrolled_clicker(client, conn, DEVICE_ID, student_id)
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


def test_unknown_device_is_enrolled_and_refused_as_unassigned(staff_db, client):
    response = post_auth(client, "NO_SUCH_DEVICE", SECRET)

    assert response.status_code == 403
    assert response.json()["detail"] == UNASSIGNED_DETAIL


def test_wrong_secret_is_refused_with_401(staff_db, client):
    _, conn = staff_db
    seed_enrolled_clicker(client, conn, DEVICE_ID, get_user_id(conn, "student1"))

    response = post_auth(client, DEVICE_ID, WRONG_SECRET)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid device credentials."


def test_registered_device_without_a_secret_is_claimed_by_its_first_secret(
    staff_db, client
):
    _, conn = staff_db
    add_clicker_by_hand(conn, DEVICE_ID, get_user_id(conn, "student1"))

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 200
    assert response.json()["username"] == "student1"


def test_full_fleet_refuses_an_unknown_device_like_a_wrong_secret(staff_db, client):
    _, conn = staff_db
    seed_enrolled_clicker(client, conn, "ESP32_WRONG", get_user_id(conn, "student1"))
    fill_fleet_to_cap(conn)

    unknown = post_auth(client, "NO_SUCH_DEVICE", SECRET)
    wrong = post_auth(client, "ESP32_WRONG", WRONG_SECRET)

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


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


def test_right_secret_on_unassigned_device_is_403_and_creates_no_session(
    staff_db, client
):
    _, conn = staff_db
    seed_enrolled_clicker(client, conn, DEVICE_ID, None)

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 403
    assert response.json()["detail"] == UNASSIGNED_DETAIL
    session_rows = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE device_id = ?", (DEVICE_ID,)
    ).fetchone()[0]
    assert session_rows == 0


def test_device_whose_student_is_soft_deleted_is_403(staff_db, client):
    _, conn = staff_db
    seed_enrolled_clicker(client, conn, DEVICE_ID, get_user_id(conn, "student1"))
    conn.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE username = 'student1'"
    )
    conn.commit()

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 403
    assert response.json()["detail"] == UNASSIGNED_DETAIL


@pytest.mark.parametrize("staff_username", ["teacher1", "admin1"])
def test_device_assigned_to_a_staff_account_is_403_and_creates_no_session(
    staff_db, client, staff_username
):
    """A row left from before role changes gave clickers back: still no token."""
    _, conn = staff_db
    seed_enrolled_clicker(client, conn, DEVICE_ID, get_user_id(conn, staff_username))

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 403
    assert response.json()["detail"] == UNASSIGNED_DETAIL
    session_rows = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE device_id = ?", (DEVICE_ID,)
    ).fetchone()[0]
    assert session_rows == 0


def test_second_authentication_ends_the_first_token(staff_db, client):
    _, conn = staff_db
    seed_enrolled_clicker(client, conn, DEVICE_ID, get_user_id(conn, "student1"))
    first = post_auth(client, DEVICE_ID, SECRET).json()["session_id"]
    second = post_auth(client, DEVICE_ID, SECRET).json()["session_id"]

    assert not clicker_token_is_live(client, bearer(first))
    assert clicker_token_is_live(client, bearer(second))


def test_phone_login_of_the_same_student_survives_clicker_authentication(
    staff_db, client
):
    _, conn = staff_db
    seed_enrolled_clicker(client, conn, DEVICE_ID, get_user_id(conn, "student1"))
    post_auth(client, DEVICE_ID, SECRET)

    phone_headers = auth_headers(client, "student1")

    response = client.get(PROFILE_URL, headers=phone_headers)
    assert response.status_code == 200


def test_secret_and_tokens_never_reach_the_logs(staff_db, client, caplog):
    _, conn = staff_db
    seed_enrolled_clicker(client, conn, DEVICE_ID, get_user_id(conn, "student1"))

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
