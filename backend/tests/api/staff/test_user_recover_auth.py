"""Authentication and RBAC authorization tests for user recovery endpoint."""

from fastapi.testclient import TestClient

from core.security.auth import hash_pin
from tests.conftest import auth_headers, get_user_id


def test_recover_user_unauthenticated(client: TestClient) -> None:
    """Unauthenticated caller receives 401 Unauthorized."""
    assert (
        client.post(
            "/api/v1/staff/users/1/recover", json={"username": "new_student"}
        ).status_code
        == 401
    )


def test_recover_user_forbidden_for_students(staff_db, client: TestClient) -> None:
    """Students cannot recover accounts (403 Forbidden)."""
    _, conn = staff_db
    student2_id = get_user_id(conn, "student2")
    student_headers = auth_headers(client, "student1", "1234")

    res = client.post(
        f"/api/v1/staff/users/{student2_id}/recover",
        headers=student_headers,
        json={"username": "new_student2"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "Insufficient permissions."


def test_teacher_recovering_admin_returns_403(staff_db, client: TestClient) -> None:
    """Teacher cannot recover an admin account (403 Forbidden)."""
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1", "1234")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Create and delete admin2
    client.post(
        "/api/v1/staff/users",
        headers=admin_headers,
        json={"username": "admin2", "pin": "1234", "role": "admin"},
    )
    admin2_id = get_user_id(conn, "admin2")
    client.delete(f"/api/v1/staff/users/{admin2_id}", headers=admin_headers)

    # Teacher attempts recovery
    rec_res = client.post(
        f"/api/v1/staff/users/{admin2_id}/recover",
        headers=teacher_headers,
        json={"username": "admin2_restored"},
    )
    assert rec_res.status_code == 403
    assert rec_res.json()["detail"] == "Only admins may recover admin accounts."


def test_teacher_recovers_another_teacher_success(staff_db, client: TestClient) -> None:
    """Under the uniform staff matrix, a teacher can recover another teacher's account."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Create teacher2
    client.post(
        "/api/v1/staff/users",
        headers=teacher_headers,
        json={"username": "teacher2", "pin": "1234", "role": "teacher"},
    )
    teacher2_id = get_user_id(conn, "teacher2")

    # Delete teacher2
    client.delete(f"/api/v1/staff/users/{teacher2_id}", headers=teacher_headers)

    # Recover teacher2
    rec_res = client.post(
        f"/api/v1/staff/users/{teacher2_id}/recover",
        headers=teacher_headers,
        json={"username": "teacher2_new"},
    )
    assert rec_res.status_code == 200
    assert rec_res.json()["username"] == "teacher2_new"


def test_admin_recovers_any_account(staff_db, client: TestClient) -> None:
    """Admin can recover student, teacher, and admin accounts."""
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1", "1234")

    # Create and delete admin2
    client.post(
        "/api/v1/staff/users",
        headers=admin_headers,
        json={"username": "admin2", "pin": "1234", "role": "admin"},
    )
    admin2_id = get_user_id(conn, "admin2")
    client.delete(f"/api/v1/staff/users/{admin2_id}", headers=admin_headers)

    # Admin recovers admin2
    rec_res = client.post(
        f"/api/v1/staff/users/{admin2_id}/recover",
        headers=admin_headers,
        json={"username": "admin2_restored"},
    )
    assert rec_res.status_code == 200
    assert rec_res.json()["username"] == "admin2_restored"


def test_recover_target_not_found_or_not_deleted(staff_db, client: TestClient) -> None:
    """Recovering non-existent or currently-active user returns 404 Not Found."""
    _, conn = staff_db
    student1_id = get_user_id(conn, "student1")
    admin_headers = auth_headers(client, "admin1", "1234")

    # Non-existent ID
    res_nonexistent = client.post(
        "/api/v1/staff/users/99999/recover",
        headers=admin_headers,
        json={"username": "some_user"},
    )
    assert res_nonexistent.status_code == 404
    assert res_nonexistent.json()["detail"] == "Deleted user not found."

    # Active user (not deleted)
    res_active = client.post(
        f"/api/v1/staff/users/{student1_id}/recover",
        headers=admin_headers,
        json={"username": "some_user"},
    )
    assert res_active.status_code == 404
    assert res_active.json()["detail"] == "Deleted user not found."


def test_recover_user_blocked_during_pending_rotation(
    temp_db, client: TestClient
) -> None:
    """Staff caller with must_change_pin=1 is blocked (403) by the rotation gate."""
    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, role, must_change_pin) "
        "VALUES ('teacher_rot', ?, 'teacher', 1)",
        (hashed,),
    )
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, role, deleted_at) "
        "VALUES ('deleted_stud', ?, 'student', CURRENT_TIMESTAMP)",
        (hashed,),
    )
    conn.commit()

    cursor.execute("SELECT id FROM users WHERE username = 'deleted_stud'")
    deleted_id = cursor.fetchone()["id"]

    login_res = client.post(
        "/api/v1/auth/login", json={"username": "teacher_rot", "pin": "1234"}
    )
    token = login_res.json()["session_id"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        f"/api/v1/staff/users/{deleted_id}/recover",
        headers=headers,
        json={"username": "restored_stud"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "PIN change required."
