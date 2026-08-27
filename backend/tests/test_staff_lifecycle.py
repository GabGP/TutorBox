import logging
import sqlite3
import uuid

from fastapi.testclient import TestClient

from src.security.auth import hash_pin, verify_pin
from tests.conftest import auth_headers


def _get_user_id(conn: sqlite3.Connection, username: str) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    assert row is not None, f"User {username} not found in test database."
    return row["id"]


# --- Soft Delete Tests ---


def test_teacher_deletes_student_success(staff_db, client: TestClient):
    """
    Teacher can soft-delete a student.
    - Returns 200 OK with 'Account deleted.'.
    - Database row has deleted_at set, former_username populated, username anonymized.
    - Old sessions are invalidated.
    - Login with old username/pin fails.
    """
    _, conn = staff_db
    student_id = _get_user_id(conn, "student1")

    # Log student1 in to create an active session
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert login_res.status_code == 200
    student_token = login_res.json()["session_id"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Verify session works
    assert client.get("/users/me", headers=student_headers).status_code == 200

    # Teacher deletes student1
    teacher_headers = auth_headers(client, "teacher1", "1234")
    del_res = client.delete(f"/users/{student_id}", headers=teacher_headers)
    assert del_res.status_code == 200
    assert del_res.json() == {"detail": "Account deleted."}

    # Active session is immediately invalidated (401)
    assert client.get("/users/me", headers=student_headers).status_code == 401

    # Login fails
    assert (
        client.post("/login", json={"username": "student1", "pin": "1234"}).status_code
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


def test_teacher_deletes_another_teacher_success(staff_db, client: TestClient):
    """
    Under the uniform staff matrix, a teacher can soft-delete another teacher.
    """
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Create teacher2
    client.post(
        "/users",
        headers=teacher_headers,
        json={"username": "teacher2", "pin": "1234", "role": "teacher"},
    )
    teacher2_id = _get_user_id(conn, "teacher2")

    del_res = client.delete(f"/users/{teacher2_id}", headers=teacher_headers)
    assert del_res.status_code == 200
    assert del_res.json() == {"detail": "Account deleted."}


def test_teacher_deleting_admin_returns_403(staff_db, client: TestClient):
    """
    Teacher cannot delete an admin account (403 Forbidden).
    """
    _, conn = staff_db
    admin_id = _get_user_id(conn, "admin1")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    res = client.delete(f"/users/{admin_id}", headers=teacher_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Only admins may delete admin accounts."


def test_admin_deletes_anyone_success(staff_db, client: TestClient):
    """
    Admin can delete students, teachers, and other admins (when not the last admin).
    """
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1", "1234")

    # Admin deletes student
    student_id = _get_user_id(conn, "student1")
    assert (
        client.delete(f"/users/{student_id}", headers=admin_headers).status_code == 200
    )

    # Admin deletes teacher
    teacher_id = _get_user_id(conn, "teacher1")
    assert (
        client.delete(f"/users/{teacher_id}", headers=admin_headers).status_code == 200
    )

    # Admin creates second admin and deletes them
    client.post(
        "/users",
        headers=admin_headers,
        json={"username": "admin2", "pin": "1234", "role": "admin"},
    )
    admin2_id = _get_user_id(conn, "admin2")
    assert (
        client.delete(f"/users/{admin2_id}", headers=admin_headers).status_code == 200
    )


def test_admin_cannot_delete_last_remaining_admin(staff_db, client: TestClient):
    """
    Last-admin guard: Appliance must never lose its final administrator (409 Conflict).
    """
    _, conn = staff_db
    admin_id = _get_user_id(conn, "admin1")
    admin_headers = auth_headers(client, "admin1", "1234")

    # Only admin1 exists
    res = client.delete(f"/users/{admin_id}", headers=admin_headers)
    assert res.status_code == 409
    assert res.json()["detail"] == "Cannot delete the last remaining admin account."


def test_delete_user_not_found(staff_db, client: TestClient):
    """
    Deleting a non-existent user returns 404 Not Found.
    """
    admin_headers = auth_headers(client, "admin1", "1234")
    res = client.delete("/users/99999", headers=admin_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found."


def test_delete_already_deleted_user_returns_404(staff_db, client: TestClient):
    """
    Deleting an already soft-deleted user returns 404 Not Found.
    """
    _, conn = staff_db
    student1_id = _get_user_id(conn, "student1")
    admin_headers = auth_headers(client, "admin1", "1234")

    # First delete succeeds
    assert (
        client.delete(f"/users/{student1_id}", headers=admin_headers).status_code == 200
    )

    # Second delete returns 404
    res = client.delete(f"/users/{student1_id}", headers=admin_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found."


def test_delete_user_forbidden_for_students(staff_db, client: TestClient):
    """
    Students cannot delete accounts (403 Forbidden).
    """
    _, conn = staff_db
    student2_id = _get_user_id(conn, "student2")
    student_headers = auth_headers(client, "student1", "1234")

    res = client.delete(f"/users/{student2_id}", headers=student_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Insufficient permissions."


def test_delete_user_unauthenticated(client: TestClient):
    """
    Unauthenticated caller receives 401 Unauthorized.
    """
    assert client.delete("/users/1").status_code == 401


def test_delete_user_blocked_during_pending_rotation(temp_db, client: TestClient):
    """
    Staff caller with must_change_pin=1 is blocked (403) by the rotation gate.
    """
    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, role, must_change_pin) VALUES ('teacher_rot', ?, 'teacher', 1)",
        (hashed,),
    )
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, role) VALUES ('target_stud', ?, 'student')",
        (hashed,),
    )
    conn.commit()

    cursor.execute("SELECT id FROM users WHERE username = 'target_stud'")
    target_id = cursor.fetchone()["id"]

    login_res = client.post("/login", json={"username": "teacher_rot", "pin": "1234"})
    token = login_res.json()["session_id"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.delete(f"/users/{target_id}", headers=headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "PIN change required."


def test_soft_delete_preserves_telemetry_turn_logs(staff_db, client: TestClient):
    """
    Telemetry preservation: turn_logs records remain intact and joinable to the soft-deleted user row.
    """
    _, conn = staff_db
    student_id = _get_user_id(conn, "student1")
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
    del_res = client.delete(f"/users/{student_id}", headers=teacher_headers)
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


def test_original_username_reusable_after_deletion(staff_db, client: TestClient):
    """
    Once an account is soft-deleted and its username anonymized, the original username
    is immediately available for new registration / creation.
    """
    _, conn = staff_db
    student_id = _get_user_id(conn, "student1")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Delete student1
    assert (
        client.delete(f"/users/{student_id}", headers=teacher_headers).status_code
        == 200
    )

    # Re-register with 'student1'
    signup_res = client.post("/signup", json={"username": "student1", "pin": "5678"})
    assert signup_res.status_code == 201
    assert signup_res.json()["username"] == "student1"


# --- Account Recovery Tests ---


def test_teacher_recovers_student_success(staff_db, client: TestClient):
    """
    Teacher can recover a soft-deleted student account with a new username.
    - Returns 200 OK with RecoverUserResponse.
    - Database row has deleted_at cleared and must_change_pin=1.
    - Student can log in with temporary PIN and is prompted for rotation.
    """
    _, conn = staff_db
    student2_id = _get_user_id(conn, "student2")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Soft-delete student2
    assert (
        client.delete(f"/users/{student2_id}", headers=teacher_headers).status_code
        == 200
    )

    # Recover student2 under new username 'student2_restored'
    rec_res = client.post(
        f"/users/{student2_id}/recover",
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
        "/login", json={"username": "student2_restored", "pin": temp_pin}
    )
    assert login_res.status_code == 200
    assert login_res.json()["must_change_pin"] is True


def test_teacher_recovers_another_teacher_success(staff_db, client: TestClient):
    """
    Under the uniform staff matrix, a teacher can recover another teacher's account.
    """
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Create teacher2
    client.post(
        "/users",
        headers=teacher_headers,
        json={"username": "teacher2", "pin": "1234", "role": "teacher"},
    )
    teacher2_id = _get_user_id(conn, "teacher2")

    # Delete teacher2
    client.delete(f"/users/{teacher2_id}", headers=teacher_headers)

    # Recover teacher2
    rec_res = client.post(
        f"/users/{teacher2_id}/recover",
        headers=teacher_headers,
        json={"username": "teacher2_new"},
    )
    assert rec_res.status_code == 200
    assert rec_res.json()["username"] == "teacher2_new"


def test_teacher_recovering_admin_returns_403(staff_db, client: TestClient):
    """
    Teacher cannot recover an admin account (403 Forbidden).
    """
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1", "1234")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Create and delete admin2
    client.post(
        "/users",
        headers=admin_headers,
        json={"username": "admin2", "pin": "1234", "role": "admin"},
    )
    admin2_id = _get_user_id(conn, "admin2")
    client.delete(f"/users/{admin2_id}", headers=admin_headers)

    # Teacher attempts recovery
    rec_res = client.post(
        f"/users/{admin2_id}/recover",
        headers=teacher_headers,
        json={"username": "admin2_restored"},
    )
    assert rec_res.status_code == 403
    assert rec_res.json()["detail"] == "Only admins may recover admin accounts."


def test_admin_recovers_any_account(staff_db, client: TestClient):
    """
    Admin can recover student, teacher, and admin accounts.
    """
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1", "1234")

    # Create and delete admin2
    client.post(
        "/users",
        headers=admin_headers,
        json={"username": "admin2", "pin": "1234", "role": "admin"},
    )
    admin2_id = _get_user_id(conn, "admin2")
    client.delete(f"/users/{admin2_id}", headers=admin_headers)

    # Admin recovers admin2
    rec_res = client.post(
        f"/users/{admin2_id}/recover",
        headers=admin_headers,
        json={"username": "admin2_restored"},
    )
    assert rec_res.status_code == 200
    assert rec_res.json()["username"] == "admin2_restored"


def test_recover_username_conflict_returns_409(staff_db, client: TestClient):
    """
    Recovering an account using an already-taken username returns 409 Conflict.
    """
    _, conn = staff_db
    student2_id = _get_user_id(conn, "student2")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Soft-delete student2
    client.delete(f"/users/{student2_id}", headers=teacher_headers)

    # Attempt to recover with taken username 'student1'
    rec_res = client.post(
        f"/users/{student2_id}/recover",
        headers=teacher_headers,
        json={"username": "student1"},
    )
    assert rec_res.status_code == 409
    assert (
        rec_res.json()["detail"]
        == "Username already taken. Choose another for this account."
    )


def test_recover_target_not_found_or_not_deleted(staff_db, client: TestClient):
    """
    Recovering non-existent or currently-active user returns 404 Not Found.
    """
    _, conn = staff_db
    student1_id = _get_user_id(conn, "student1")
    admin_headers = auth_headers(client, "admin1", "1234")

    # Non-existent ID
    res_nonexistent = client.post(
        "/users/99999/recover",
        headers=admin_headers,
        json={"username": "some_user"},
    )
    assert res_nonexistent.status_code == 404
    assert res_nonexistent.json()["detail"] == "Deleted user not found."

    # Active user (not deleted)
    res_active = client.post(
        f"/users/{student1_id}/recover",
        headers=admin_headers,
        json={"username": "some_user"},
    )
    assert res_active.status_code == 404
    assert res_active.json()["detail"] == "Deleted user not found."


def test_recover_validation_errors(staff_db, client: TestClient):
    """
    POST /users/{id}/recover validates username format (422 Unprocessable Entity).
    """
    _, conn = staff_db
    student2_id = _get_user_id(conn, "student2")
    teacher_headers = auth_headers(client, "teacher1", "1234")
    client.delete(f"/users/{student2_id}", headers=teacher_headers)

    # Invalid username with space
    res = client.post(
        f"/users/{student2_id}/recover",
        headers=teacher_headers,
        json={"username": "bad name"},
    )
    assert res.status_code == 422


def test_recover_user_forbidden_for_students(staff_db, client: TestClient):
    """
    Students cannot recover accounts (403 Forbidden).
    """
    _, conn = staff_db
    student2_id = _get_user_id(conn, "student2")
    student_headers = auth_headers(client, "student1", "1234")

    res = client.post(
        f"/users/{student2_id}/recover",
        headers=student_headers,
        json={"username": "new_student2"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "Insufficient permissions."


def test_recover_user_unauthenticated(client: TestClient):
    """
    Unauthenticated caller receives 401 Unauthorized.
    """
    assert (
        client.post("/users/1/recover", json={"username": "new_student"}).status_code
        == 401
    )


def test_recover_user_blocked_during_pending_rotation(temp_db, client: TestClient):
    """
    Staff caller with must_change_pin=1 is blocked (403) by the rotation gate.
    """
    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, role, must_change_pin) VALUES ('teacher_rot', ?, 'teacher', 1)",
        (hashed,),
    )
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, role, deleted_at) VALUES ('deleted_stud', ?, 'student', CURRENT_TIMESTAMP)",
        (hashed,),
    )
    conn.commit()

    cursor.execute("SELECT id FROM users WHERE username = 'deleted_stud'")
    deleted_id = cursor.fetchone()["id"]

    login_res = client.post("/login", json={"username": "teacher_rot", "pin": "1234"})
    token = login_res.json()["session_id"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        f"/users/{deleted_id}/recover",
        headers=headers,
        json={"username": "restored_stud"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "PIN change required."


def test_recover_temporary_pin_never_logged(staff_db, client: TestClient, caplog):
    """
    SECURITY PROOF:
    The temporary PIN generated during account recovery must never appear in any log output.
    """
    _, conn = staff_db
    student2_id = _get_user_id(conn, "student2")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Soft-delete student2
    client.delete(f"/users/{student2_id}", headers=teacher_headers)

    # Recover student2 under caplog
    with caplog.at_level(logging.DEBUG):
        rec_res = client.post(
            f"/users/{student2_id}/recover",
            headers=teacher_headers,
            json={"username": "student2_restored"},
        )

    assert rec_res.status_code == 200
    temp_pin = rec_res.json()["temporary_pin"]

    for record in caplog.records:
        assert temp_pin not in record.getMessage(), (
            f"Security violation: Temporary PIN leaked in log message: '{record.getMessage()}'"
        )
