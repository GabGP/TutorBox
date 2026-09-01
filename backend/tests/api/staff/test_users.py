from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_list_users_active_only(staff_db, client: TestClient):
    """
    GET /users lists active users and hides deleted accounts by default.
    """
    _, conn = staff_db
    cursor = conn.cursor()
    # Soft-delete student2
    cursor.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP, former_username = 'student2' WHERE username = 'student2'"
    )
    conn.commit()

    headers = auth_headers(client, "teacher1", "1234")
    res = client.get("/api/v1/staff/users", headers=headers)
    assert res.status_code == 200
    usernames = [u["username"] for u in res.json()["users"]]
    assert "student1" in usernames
    assert "teacher1" in usernames
    assert "admin1" in usernames
    assert "student2" not in usernames


def test_list_users_include_deleted(staff_db, client: TestClient):
    """
    GET /users?include_deleted=true lists deleted accounts with minimal recovery metadata.
    """
    _, conn = staff_db
    cursor = conn.cursor()
    # Soft-delete student2
    cursor.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP, former_username = 'student2' WHERE username = 'student2'"
    )
    conn.commit()

    headers = auth_headers(client, "teacher1", "1234")
    res = client.get("/api/v1/staff/users?include_deleted=true", headers=headers)
    assert res.status_code == 200
    users = res.json()["users"]
    assert len(users) == 1
    deleted = users[0]
    assert deleted["former_username"] == "student2"
    assert deleted["role"] == "student"
    assert deleted["deleted_at"] is not None
    assert "hashed_pin" not in deleted


def test_create_student_by_teacher(staff_db, client: TestClient):
    """
    Teacher can create a student account (201 Created) with must_change_pin=0.
    """
    _, conn = staff_db
    headers = auth_headers(client, "teacher1", "1234")
    res = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "new_student", "pin": "1234", "role": "student"},
    )
    assert res.status_code == 201
    assert res.json() == {"username": "new_student", "role": "student"}

    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, must_change_pin, deleted_at FROM users WHERE username = 'new_student'"
    )
    row = cursor.fetchone()
    assert row is not None
    assert row["role"] == "student"
    assert row["must_change_pin"] == 0
    assert row["deleted_at"] is None


def test_create_teacher_by_teacher(staff_db, client: TestClient):
    """
    Teacher can create another teacher account (201 Created).
    """
    headers = auth_headers(client, "teacher1", "1234")
    res = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "teacher2", "pin": "1234", "role": "teacher"},
    )
    assert res.status_code == 201
    assert res.json() == {"username": "teacher2", "role": "teacher"}


def test_teacher_creating_admin_returns_403(staff_db, client: TestClient):
    """
    Teacher attempting to create an admin account is blocked with 403 Forbidden.
    """
    headers = auth_headers(client, "teacher1", "1234")
    res = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "admin2", "pin": "1234", "role": "admin"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "Only admins may create admin accounts."


def test_create_any_role_by_admin(staff_db, client: TestClient):
    """
    Admin can create accounts of any role: student, teacher, and admin.
    """
    headers = auth_headers(client, "admin1", "1234")

    # Admin creates student
    res_student = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "adm_student", "pin": "1234", "role": "student"},
    )
    assert res_student.status_code == 201

    # Admin creates teacher
    res_teacher = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "adm_teacher", "pin": "1234", "role": "teacher"},
    )
    assert res_teacher.status_code == 201

    # Admin creates admin
    res_admin = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "adm_admin", "pin": "1234", "role": "admin"},
    )
    assert res_admin.status_code == 201


def test_create_user_duplicate_returns_409(staff_db, client: TestClient):
    """
    POST /users with an existing username returns 409 Conflict.
    """
    headers = auth_headers(client, "admin1", "1234")
    res = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "student1", "pin": "1234", "role": "student"},
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "Username already taken."


def test_create_user_validation_errors(staff_db, client: TestClient):
    """
    POST /users validates username, pin, and role fields (422 Unprocessable Entity).
    """
    headers = auth_headers(client, "admin1", "1234")

    # Invalid username format
    res = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "bad name", "pin": "1234", "role": "student"},
    )
    assert res.status_code == 422

    # Invalid PIN format
    res = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "valid_user", "pin": "abcd", "role": "student"},
    )
    assert res.status_code == 422

    # Invalid role
    res = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "valid_user", "pin": "1234", "role": "superadmin"},
    )
    assert res.status_code == 422


def test_staff_endpoints_forbidden_for_students(staff_db, client: TestClient):
    """
    Student role is forbidden (403) from accessing GET /users and POST /users.
    """
    headers = auth_headers(client, "student1", "1234")

    res_get = client.get("/api/v1/staff/users", headers=headers)
    assert res_get.status_code == 403
    assert res_get.json()["detail"] == "Insufficient permissions."

    res_post = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "another_user", "pin": "1234", "role": "student"},
    )
    assert res_post.status_code == 403
    assert res_post.json()["detail"] == "Insufficient permissions."


def test_staff_endpoints_unauthenticated(client: TestClient):
    """
    Unauthenticated callers receive 401 Unauthorized.
    """
    assert client.get("/api/v1/staff/users").status_code == 401
    assert (
        client.post(
            "/api/v1/staff/users",
            json={"username": "another_user", "pin": "1234", "role": "student"},
        ).status_code
        == 401
    )


def test_staff_endpoints_blocked_during_pending_rotation(temp_db, client: TestClient):
    """
    Staff caller with must_change_pin=1 is blocked (403) by the rotation gate.
    """
    from src.security.auth import hash_pin

    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, role, must_change_pin) VALUES ('teacher_rot', ?, 'teacher', 1)",
        (hashed,),
    )
    conn.commit()

    login_res = client.post(
        "/api/v1/auth/login", json={"username": "teacher_rot", "pin": "1234"}
    )
    token = login_res.json()["session_id"]
    headers = {"Authorization": f"Bearer {token}"}

    res_get = client.get("/api/v1/staff/users", headers=headers)
    assert res_get.status_code == 403
    assert res_get.json()["detail"] == "PIN change required."

    res_post = client.post(
        "/api/v1/staff/users",
        headers=headers,
        json={"username": "some_user", "pin": "1234", "role": "student"},
    )
    assert res_post.status_code == 403
    assert res_post.json()["detail"] == "PIN change required."
