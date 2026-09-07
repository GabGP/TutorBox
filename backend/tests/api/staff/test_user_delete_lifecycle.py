"""Lifecycle, telemetry preservation, and anonymization tests for user deletion."""

import uuid

from fastapi.testclient import TestClient

from core.security.auth import verify_pin
from tests.conftest import auth_headers, get_user_id


def test_teacher_deletes_student_success(staff_db, client: TestClient) -> None:
    """Teacher can soft-delete a student.

    - Returns 200 OK with 'Account deleted.'.
    - Database row has deleted_at set, former_username populated, username anonymized.
    - Old sessions are invalidated.
    - Login with old username/pin fails.
    """
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")

    # Log student1 in to create an active session
    login_res = client.post(
        "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
    )
    assert login_res.status_code == 200
    student_token = login_res.json()["session_id"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Verify session works
    assert client.get("/api/v1/users/me", headers=student_headers).status_code == 200

    # Teacher deletes student1
    teacher_headers = auth_headers(client, "teacher1", "1234")
    del_res = client.delete(
        f"/api/v1/staff/users/{student_id}", headers=teacher_headers
    )
    assert del_res.status_code == 200
    assert del_res.json() == {"detail": "Account deleted."}

    # Active session is immediately invalidated (401)
    assert client.get("/api/v1/users/me", headers=student_headers).status_code == 401

    # Login fails
    assert (
        client.post(
            "/api/v1/auth/login", json={"username": "student1", "pin": "1234"}
        ).status_code
        == 401
    )

    # Inspect DB record
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, former_username, hashed_pin, deleted_at FROM users WHERE id = ?",
        (student_id,),
    )
    row = cursor.fetchone()
    assert row["deleted_at"] is not None
    assert row["former_username"] == "student1"
    assert row["username"].startswith(f"deleted_user_{student_id}_")
    # Verify the anonymized hash fails any PIN check cleanly without exceptions
    assert verify_pin("1234", row["hashed_pin"]) is False


def test_delete_already_deleted_user_returns_404(staff_db, client: TestClient) -> None:
    """Deleting an already soft-deleted user returns 404 Not Found."""
    _, conn = staff_db
    student1_id = get_user_id(conn, "student1")
    admin_headers = auth_headers(client, "admin1", "1234")

    # First delete succeeds
    assert (
        client.delete(
            f"/api/v1/staff/users/{student1_id}", headers=admin_headers
        ).status_code
        == 200
    )

    # Second delete returns 404
    res = client.delete(f"/api/v1/staff/users/{student1_id}", headers=admin_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found."


def test_soft_delete_preserves_telemetry_turn_logs(
    staff_db, client: TestClient
) -> None:
    """Telemetry preservation: turn_logs records remain intact and joinable to user."""
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    session_id = str(uuid.uuid4())

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (id, user_id, is_active) VALUES (?, ?, 1)",
        (session_id, student_id),
    )
    cursor.execute(
        "INSERT INTO turn_logs (session_id, user_input, final_response) VALUES (?, ?, ?)",
        (session_id, "2 + 2", "4"),
    )
    conn.commit()

    # Teacher deletes student1
    teacher_headers = auth_headers(client, "teacher1", "1234")
    del_res = client.delete(
        f"/api/v1/staff/users/{student_id}", headers=teacher_headers
    )
    assert del_res.status_code == 200

    # Verify telemetry is intact
    cursor.execute(
        "SELECT t.id, t.user_input, u.former_username, u.deleted_at "
        "FROM turn_logs t "
        "JOIN sessions s ON s.id = t.session_id "
        "JOIN users u ON u.id = s.user_id "
        "WHERE u.id = ?",
        (student_id,),
    )
    row = cursor.fetchone()
    assert row is not None
    assert row["user_input"] == "2 + 2"
    assert row["former_username"] == "student1"
    assert row["deleted_at"] is not None


def test_original_username_reusable_after_deletion(
    staff_db, client: TestClient
) -> None:
    """Once an account is soft-deleted, original username is immediately available."""
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Delete student1
    assert (
        client.delete(
            f"/api/v1/staff/users/{student_id}", headers=teacher_headers
        ).status_code
        == 200
    )

    # Re-register with 'student1'
    signup_res = client.post(
        "/api/v1/users/signup", json={"username": "student1", "pin": "5678"}
    )
    assert signup_res.status_code == 201
    assert signup_res.json()["username"] == "student1"
