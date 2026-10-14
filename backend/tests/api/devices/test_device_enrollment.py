"""Clicker enrollment: the first secret a clicker sends is kept, and no later login replaces it.

The clicker makes its own secret, so staff never see or issue one. A device added by hand
with no secret is claimed by its first secret. The fleet holds at most MAX_DEVICES.
"""

import logging
import sqlite3

from fastapi.testclient import TestClient

from api.devices.enrollment import MAX_DEVICES
from core.db.device_repository import count_devices
from core.security import token_digest
from core.security.rate_limit import MAX_ATTEMPTS
from tests.api.session.fleet_support import (
    assign_device,
    bearer,
    cast_vote,
    start_match,
    stored_votes,
)
from tests.conftest import auth_headers, get_user_id, required

AUTH_URL = "/api/v1/devices/auth"
DEVICES_URL = "/api/v1/staff/devices"
DEVICE_ID = "ESP32-A4CF12"
SECRET = "0123456789abcdef0123456789abcdef"
WRONG_SECRET = "fedcba9876543210fedcba9876543210"
UNASSIGNED_DETAIL = "Device is not assigned to any student."
INVALID_CREDENTIALS_DETAIL = "Invalid device credentials."


def post_auth(client: TestClient, device_id: str, secret: str):
    return client.post(AUTH_URL, json={"device_id": device_id, "secret": secret})


def read_device_row(conn: sqlite3.Connection, device_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT device_id, assigned_user_id, secret_hash, secret_issued_at "
        "FROM devices WHERE device_id = ?",
        (device_id,),
    ).fetchone()


def read_enrollment_audit_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT actor_user_id, target_user_id FROM audit_logs "
        "WHERE action = 'device_enrolled' ORDER BY id"
    ).fetchall()


def fill_fleet_to_cap(conn: sqlite3.Connection) -> None:
    """Adds clickers with no secret until the fleet holds MAX_DEVICES."""
    for number in range(count_devices(conn), MAX_DEVICES):
        conn.execute(
            "INSERT INTO devices (device_id) VALUES (?)", (f"FILLER-{number}",)
        )
    conn.commit()


def test_unknown_device_is_enrolled_on_first_contact_and_refused_as_unassigned(
    staff_db, client
):
    _, conn = staff_db

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 403
    assert response.json()["detail"] == UNASSIGNED_DETAIL
    row = read_device_row(conn, DEVICE_ID)
    assert row is not None
    assert row["secret_hash"] == token_digest(SECRET)
    assert row["secret_hash"] != SECRET
    assert row["secret_issued_at"] is not None
    assert row["assigned_user_id"] is None


def test_same_secret_again_is_refused_as_unassigned_and_adds_no_second_enrollment(
    staff_db, client
):
    _, conn = staff_db
    post_auth(client, DEVICE_ID, SECRET)

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 403
    assert count_devices(conn) == 1
    assert len(read_enrollment_audit_rows(conn)) == 1


def test_wrong_secret_after_enrollment_is_refused_and_keeps_the_stored_digest(
    staff_db, client
):
    _, conn = staff_db
    post_auth(client, DEVICE_ID, SECRET)

    response = post_auth(client, DEVICE_ID, WRONG_SECRET)

    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_CREDENTIALS_DETAIL
    assert required(read_device_row(conn, DEVICE_ID))["secret_hash"] == token_digest(
        SECRET
    )


def test_wrong_secrets_after_enrollment_count_toward_the_lockout(staff_db, client):
    post_auth(client, DEVICE_ID, SECRET)
    for _ in range(MAX_ATTEMPTS):
        assert post_auth(client, DEVICE_ID, WRONG_SECRET).status_code == 401

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 429


def test_hand_added_device_is_claimed_by_its_first_secret_and_refuses_another(
    staff_db, client
):
    _, conn = staff_db
    registered = client.post(
        DEVICES_URL,
        json={"device_id": DEVICE_ID},
        headers=auth_headers(client, "teacher1"),
    )
    assert registered.status_code == 201

    first_contact = post_auth(client, DEVICE_ID, SECRET)
    second_contact = post_auth(client, DEVICE_ID, WRONG_SECRET)

    assert first_contact.status_code == 403
    assert second_contact.status_code == 401
    assert required(read_device_row(conn, DEVICE_ID))["secret_hash"] == token_digest(
        SECRET
    )


def test_hand_added_and_assigned_device_logs_in_on_its_first_contact(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    client.post(DEVICES_URL, json={"device_id": DEVICE_ID}, headers=teacher)
    student_id = get_user_id(conn, "student1")
    assert assign_device(client, teacher, DEVICE_ID, student_id).status_code == 200

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 200
    assert response.json()["username"] == "student1"
    assert response.json()["device_id"] == DEVICE_ID


def test_full_fleet_refuses_an_unknown_device_with_401_and_creates_no_row(
    staff_db, client, caplog
):
    _, conn = staff_db
    fill_fleet_to_cap(conn)

    with caplog.at_level(logging.WARNING):
        response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_CREDENTIALS_DETAIL
    assert count_devices(conn) == MAX_DEVICES
    assert read_device_row(conn, DEVICE_ID) is None
    assert read_enrollment_audit_rows(conn) == []
    assert f"Refused to enroll device '{DEVICE_ID}'" in caplog.text


def test_full_fleet_still_lets_a_hand_added_device_be_claimed(staff_db, client):
    _, conn = staff_db
    registered = client.post(
        DEVICES_URL,
        json={"device_id": DEVICE_ID},
        headers=auth_headers(client, "teacher1"),
    )
    assert registered.status_code == 201
    fill_fleet_to_cap(conn)

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 403
    assert response.json()["detail"] == UNASSIGNED_DETAIL
    assert required(read_device_row(conn, DEVICE_ID))["secret_hash"] == token_digest(
        SECRET
    )
    assert count_devices(conn) == MAX_DEVICES


def test_enrolled_clicker_votes_as_hardware_once_assigned(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    post_auth(client, DEVICE_ID, SECRET)
    assert assign_device(client, teacher, DEVICE_ID, student_id).status_code == 200
    login = post_auth(client, DEVICE_ID, SECRET)
    session_id = start_match(client, conn, teacher, question_count=1)

    vote = cast_vote(client, session_id, bearer(login.json()["session_id"]), "A")

    assert login.status_code == 200
    assert vote.status_code == 200
    stored = [
        (row["student_id"], row["transport_type"], row["device_id"])
        for row in stored_votes(conn, session_id)
    ]
    assert stored == [(student_id, "hardware", DEVICE_ID)]


def test_deleted_device_enrolls_again_with_the_same_secret(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    post_auth(client, DEVICE_ID, SECRET)
    deleted = client.delete(f"{DEVICES_URL}/{DEVICE_ID}", headers=teacher)
    assert deleted.status_code == 200
    assert read_device_row(conn, DEVICE_ID) is None

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 403
    assert response.json()["detail"] == UNASSIGNED_DETAIL
    row = required(read_device_row(conn, DEVICE_ID))
    assert row["secret_hash"] == token_digest(SECRET)
    assert row["assigned_user_id"] is None
    assert len(read_enrollment_audit_rows(conn)) == 2


def test_enrollment_audit_row_has_no_actor_and_no_target(staff_db, client):
    _, conn = staff_db

    post_auth(client, DEVICE_ID, SECRET)

    rows = read_enrollment_audit_rows(conn)
    assert [(row["actor_user_id"], row["target_user_id"]) for row in rows] == [
        (None, None)
    ]


def test_secret_and_its_digest_never_reach_the_log(staff_db, client, caplog):
    with caplog.at_level(logging.DEBUG):
        post_auth(client, DEVICE_ID, SECRET)
        post_auth(client, DEVICE_ID, WRONG_SECRET)

    assert f"Device '{DEVICE_ID}' enrolled." in caplog.text
    for sensitive_value in (
        SECRET,
        WRONG_SECRET,
        token_digest(SECRET),
        token_digest(WRONG_SECRET),
    ):
        assert sensitive_value not in caplog.text
