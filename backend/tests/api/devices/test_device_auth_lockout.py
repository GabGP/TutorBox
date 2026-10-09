"""Clicker lockout: wrong secrets lock a device on one address, never a student's login."""

import sqlite3

from fastapi.testclient import TestClient

from core.db.device_repository import store_device_secret
from core.security import token_digest
from core.security.rate_limit import MAX_ATTEMPTS
from tests.conftest import get_user_id

AUTH_URL = "/api/v1/devices/auth"
DEVICE_ID = "ESP32_01"
SECRET = "0123456789abcdef0123456789abcdef"
WRONG_SECRET = "fedcba9876543210fedcba9876543210"
UNASSIGNED_DETAIL = "Device is not assigned to any student."


def seed_clicker(
    conn: sqlite3.Connection, device_id: str, assigned_user_id: int | None
) -> None:
    """Registers a clicker that has been issued SECRET."""
    conn.execute(
        "INSERT INTO devices (device_id, assigned_user_id) VALUES (?, ?)",
        (device_id, assigned_user_id),
    )
    store_device_secret(conn, device_id, token_digest(SECRET))
    conn.commit()


def post_auth(client: TestClient, device_id: str, secret: str):
    return client.post(AUTH_URL, json={"device_id": device_id, "secret": secret})


def test_device_locked_after_max_wrong_secrets_refuses_the_right_secret(
    staff_db, client
):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, get_user_id(conn, "student1"))
    for _ in range(MAX_ATTEMPTS):
        assert post_auth(client, DEVICE_ID, WRONG_SECRET).status_code == 401

    response = post_auth(client, DEVICE_ID, SECRET)

    assert response.status_code == 429
    assert "Too many failed login attempts" in response.json()["detail"]


def test_right_secret_before_the_limit_clears_the_failure_count(staff_db, client):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, get_user_id(conn, "student1"))
    for _ in range(MAX_ATTEMPTS - 1):
        assert post_auth(client, DEVICE_ID, WRONG_SECRET).status_code == 401
    assert post_auth(client, DEVICE_ID, SECRET).status_code == 200

    for _ in range(MAX_ATTEMPTS - 1):
        assert post_auth(client, DEVICE_ID, WRONG_SECRET).status_code == 401


def test_repeated_unassigned_refusals_never_lock_the_device_out(staff_db, client):
    _, conn = staff_db
    seed_clicker(conn, DEVICE_ID, None)

    for _ in range(MAX_ATTEMPTS + 2):
        response = post_auth(client, DEVICE_ID, SECRET)
        assert response.status_code == 403
        assert response.json()["detail"] == UNASSIGNED_DETAIL


def test_locking_a_device_named_like_a_user_leaves_that_users_login_open(
    staff_db, client
):
    _, conn = staff_db
    seed_clicker(conn, "student1", get_user_id(conn, "student2"))
    for _ in range(MAX_ATTEMPTS):
        assert post_auth(client, "student1", WRONG_SECRET).status_code == 401
    assert post_auth(client, "student1", SECRET).status_code == 429

    login = client.post(
        "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
    )

    assert login.status_code == 200
