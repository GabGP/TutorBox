"""Authentication and RBAC authorization tests for user deletion endpoint."""

from fastapi.testclient import TestClient

from core.security.auth import hash_pin
from tests.conftest import auth_headers, get_user_id


def test_delete_user_unauthenticated(client: TestClient) -> None:
    """Unauthenticated caller receives 401 Unauthorized."""
    assert client.delete("/api/v1/staff/users/1").status_code == 401


def test_delete_user_forbidden_for_students(staff_db, client: TestClient) -> None:
    """Students cannot delete accounts (403 Forbidden)."""
    _, conn = staff_db
    student2_id = get_user_id(conn, "student2")
    student_headers = auth_headers(client, "student1", "1234")

    res = client.delete(f"/api/v1/staff/users/{student2_id}", headers=student_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Insufficient permissions."


def test_teacher_deleting_admin_returns_403(staff_db, client: TestClient) -> None:
    """Teacher cannot delete an admin account (403 Forbidden)."""
    _, conn = staff_db
    admin_id = get_user_id(conn, "admin1")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    res = client.delete(f"/api/v1/staff/users/{admin_id}", headers=teacher_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Only admins may delete admin accounts."


def test_delete_user_not_found(staff_db, client: TestClient) -> None:
    """Deleting a non-existent user returns 404 Not Found."""
    admin_headers = auth_headers(client, "admin1", "1234")
    res = client.delete("/api/v1/staff/users/99999", headers=admin_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found."


def test_admin_cannot_delete_last_remaining_admin(staff_db, client: TestClient) -> None:
    """Last-admin guard: Appliance must never lose its final administrator (409 Conflict)."""
    _, conn = staff_db
    admin_id = get_user_id(conn, "admin1")
    admin_headers = auth_headers(client, "admin1", "1234")

    # Only admin1 exists
    res = client.delete(f"/api/v1/staff/users/{admin_id}", headers=admin_headers)
    assert res.status_code == 409
    assert res.json()["detail"] == "Cannot delete the last remaining admin account."


def test_delete_user_blocked_during_pending_rotation(
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
        "INSERT INTO users (username, hashed_pin, role) VALUES ('target_stud', ?, 'student')",
        (hashed,),
    )
    conn.commit()

    cursor.execute("SELECT id FROM users WHERE username = 'target_stud'")
    target_id = cursor.fetchone()["id"]

    login_res = client.post(
        "/api/v1/auth/login", json={"username": "teacher_rot", "pin": "1234"}
    )
    token = login_res.json()["session_id"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.delete(f"/api/v1/staff/users/{target_id}", headers=headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "PIN change required."


def test_teacher_deletes_another_teacher_success(staff_db, client: TestClient) -> None:
    """Under the uniform staff matrix, a teacher can soft-delete another teacher."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Create teacher2
    client.post(
        "/api/v1/staff/users",
        headers=teacher_headers,
        json={"username": "teacher2", "pin": "1234", "role": "teacher"},
    )
    teacher2_id = get_user_id(conn, "teacher2")

    del_res = client.delete(
        f"/api/v1/staff/users/{teacher2_id}", headers=teacher_headers
    )
    assert del_res.status_code == 200
    assert del_res.json() == {"detail": "Account deleted."}


def test_admin_deletes_anyone_success(staff_db, client: TestClient) -> None:
    """Admin can delete students, teachers, and other admins (when not the last admin)."""
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1", "1234")

    # Admin deletes student
    student_id = get_user_id(conn, "student1")
    assert (
        client.delete(
            f"/api/v1/staff/users/{student_id}", headers=admin_headers
        ).status_code
        == 200
    )

    # Admin deletes teacher
    teacher_id = get_user_id(conn, "teacher1")
    assert (
        client.delete(
            f"/api/v1/staff/users/{teacher_id}", headers=admin_headers
        ).status_code
        == 200
    )

    # Admin creates second admin and deletes them
    client.post(
        "/api/v1/staff/users",
        headers=admin_headers,
        json={"username": "admin2", "pin": "1234", "role": "admin"},
    )
    admin2_id = get_user_id(conn, "admin2")
    assert (
        client.delete(
            f"/api/v1/staff/users/{admin2_id}", headers=admin_headers
        ).status_code
        == 200
    )
