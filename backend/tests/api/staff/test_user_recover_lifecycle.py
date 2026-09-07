"""Lifecycle, credential reset, and security tests for user recovery."""

import logging

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, get_user_id


def test_teacher_recovers_student_success(staff_db, client: TestClient) -> None:
    """Teacher can recover a soft-deleted student account with a new username."""
    _, conn = staff_db
    student2_id = get_user_id(conn, "student2")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Soft-delete student2
    del_res = client.delete(
        f"/api/v1/staff/users/{student2_id}", headers=teacher_headers
    )
    assert del_res.status_code == 200

    # Recover student2 under new username 'student2_restored'
    rec_res = client.post(
        f"/api/v1/staff/users/{student2_id}/recover",
        headers=teacher_headers,
        json={"username": "student2_restored"},
    )
    assert rec_res.status_code == 200
    data = rec_res.json()
    assert data["username"] == "student2_restored"
    temp_pin = data["temporary_pin"]
    assert len(temp_pin) == 6
    assert temp_pin.isdigit()
    assert data["detail"] == "Account recovered. User must set a new PIN on next login."

    # Inspect DB record
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, deleted_at, must_change_pin FROM users WHERE id = ?",
        (student2_id,),
    )
    row = cursor.fetchone()
    assert row["username"] == "student2_restored"
    assert row["deleted_at"] is None
    assert row["must_change_pin"] == 1

    # Login with temp PIN works and flags must_change_pin=True
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "student2_restored", "pin": temp_pin},
    )
    assert login_res.status_code == 200
    assert login_res.json()["must_change_pin"] is True


def test_recover_username_conflict_returns_409(staff_db, client: TestClient) -> None:
    """Recovering an account using an already-taken username returns 409 Conflict."""
    _, conn = staff_db
    student2_id = get_user_id(conn, "student2")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Soft-delete student2
    client.delete(f"/api/v1/staff/users/{student2_id}", headers=teacher_headers)

    # Attempt to recover with taken username 'student1'
    rec_res = client.post(
        f"/api/v1/staff/users/{student2_id}/recover",
        headers=teacher_headers,
        json={"username": "student1"},
    )
    assert rec_res.status_code == 409
    assert (
        rec_res.json()["detail"]
        == "Username already taken. Choose another for this account."
    )


def test_recover_validation_errors(staff_db, client: TestClient) -> None:
    """POST /users/{id}/recover validates username format (422 Unprocessable Entity)."""
    _, conn = staff_db
    student2_id = get_user_id(conn, "student2")
    teacher_headers = auth_headers(client, "teacher1", "1234")
    client.delete(f"/api/v1/staff/users/{student2_id}", headers=teacher_headers)

    # Invalid username with space
    res = client.post(
        f"/api/v1/staff/users/{student2_id}/recover",
        headers=teacher_headers,
        json={"username": "bad name"},
    )
    assert res.status_code == 422


def test_recover_temporary_pin_never_logged(
    staff_db, client: TestClient, caplog
) -> None:
    """SECURITY PROOF:

    The temporary PIN generated during account recovery must never appear in any log output.
    """
    _, conn = staff_db
    student2_id = get_user_id(conn, "student2")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Soft-delete student2
    client.delete(f"/api/v1/staff/users/{student2_id}", headers=teacher_headers)

    # Recover student2 under caplog
    with caplog.at_level(logging.DEBUG):
        rec_res = client.post(
            f"/api/v1/staff/users/{student2_id}/recover",
            headers=teacher_headers,
            json={"username": "student2_restored"},
        )

    assert rec_res.status_code == 200
    temp_pin = rec_res.json()["temporary_pin"]

    for record in caplog.records:
        assert temp_pin not in record.getMessage(), (
            "Security violation: Temporary PIN leaked in log message: "
            f"'{record.getMessage()}'"
        )
