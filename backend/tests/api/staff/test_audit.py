from fastapi.testclient import TestClient

from tests.conftest import auth_headers, get_user_id


def test_read_audit_logs_admin_success(staff_db, client: TestClient):
    """
    Admin can read audit logs (200 OK).
    """
    admin_headers = auth_headers(client, "admin1", "1234")
    res = client.get("/audit-logs", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "logs" in data
    assert isinstance(data["logs"], list)


def test_read_audit_logs_teacher_forbidden(staff_db, client: TestClient):
    """
    Teachers are forbidden from viewing audit logs (403 Forbidden).
    """
    teacher_headers = auth_headers(client, "teacher1", "1234")
    res = client.get("/audit-logs", headers=teacher_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Insufficient permissions."


def test_read_audit_logs_student_forbidden(staff_db, client: TestClient):
    """
    Students are forbidden from viewing audit logs (403 Forbidden).
    """
    student_headers = auth_headers(client, "student1", "1234")
    res = client.get("/audit-logs", headers=student_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Insufficient permissions."


def test_read_audit_logs_unauthenticated(client: TestClient):
    """
    Unauthenticated caller receives 401 Unauthorized.
    """
    res = client.get("/audit-logs")
    assert res.status_code == 401


def test_read_audit_logs_blocked_during_pending_rotation(temp_db, client: TestClient):
    """
    Admin caller with must_change_pin=1 is blocked (403) by the rotation gate.
    """
    from src.security.auth import hash_pin

    _, conn = temp_db
    hashed = hash_pin("1234")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_pin, role, must_change_pin) VALUES ('admin_rot', ?, 'admin', 1)",
        (hashed,),
    )
    conn.commit()

    login_res = client.post("/login", json={"username": "admin_rot", "pin": "1234"})
    token = login_res.json()["session_id"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/audit-logs", headers=headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "PIN change required."


def test_audit_trail_captures_all_lifecycle_actions(staff_db, client: TestClient):
    """
    Comprehensive verification: All 7 lifecycle mutations record audit entries.
    1. signup
    2. user_created
    3. pin_reset
    4. username_changed
    5. pin_changed
    6. account_deleted
    7. account_recovered
    """
    _, conn = staff_db
    admin_id = get_user_id(conn, "admin1")
    teacher_id = get_user_id(conn, "teacher1")
    admin_headers = auth_headers(client, "admin1", "1234")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # 1. Signup
    signup_res = client.post(
        "/signup", json={"username": "audit_student", "pin": "1234"}
    )
    assert signup_res.status_code == 201
    audit_student_id = get_user_id(conn, "audit_student")

    # 2. Staff user creation
    create_res = client.post(
        "/users",
        headers=admin_headers,
        json={"username": "audit_staff_user", "pin": "1234", "role": "student"},
    )
    assert create_res.status_code == 201
    audit_staff_user_id = get_user_id(conn, "audit_staff_user")

    # 3. Staff reset PIN
    reset_res = client.post(
        f"/users/{audit_staff_user_id}/reset-pin",
        headers=teacher_headers,
    )
    assert reset_res.status_code == 200

    # 4. Username changed
    stud_login = client.post(
        "/login", json={"username": "audit_student", "pin": "1234"}
    )
    stud_token = stud_login.json()["session_id"]
    change_user_res = client.patch(
        "/users/me/username",
        headers={"Authorization": f"Bearer {stud_token}"},
        json={"current_pin": "1234", "new_username": "audit_student_renamed"},
    )
    assert change_user_res.status_code == 200

    # 5. PIN changed
    renamed_login = client.post(
        "/login", json={"username": "audit_student_renamed", "pin": "1234"}
    )
    renamed_token = renamed_login.json()["session_id"]
    change_pin_res = client.patch(
        "/users/me/pin",
        headers={"Authorization": f"Bearer {renamed_token}"},
        json={"current_pin": "1234", "new_pin": "9876"},
    )
    assert change_pin_res.status_code == 200

    # 6. Account deleted
    del_res = client.delete(
        f"/users/{audit_staff_user_id}",
        headers=admin_headers,
    )
    assert del_res.status_code == 200

    # 7. Account recovered
    rec_res = client.post(
        f"/users/{audit_staff_user_id}/recover",
        headers=admin_headers,
        json={"username": "audit_staff_recovered"},
    )
    assert rec_res.status_code == 200

    # Read audit logs as admin
    audit_res = client.get("/audit-logs", headers=admin_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()["logs"]

    # Map actions from logs
    action_map = {log["action"]: log for log in logs}

    assert "signup" in action_map
    assert action_map["signup"]["actor_user_id"] is None
    assert action_map["signup"]["target_user_id"] == audit_student_id

    assert "user_created" in action_map
    assert action_map["user_created"]["actor_user_id"] == admin_id
    assert action_map["user_created"]["target_user_id"] == audit_staff_user_id

    assert "pin_reset" in action_map
    assert action_map["pin_reset"]["actor_user_id"] == teacher_id
    assert action_map["pin_reset"]["target_user_id"] == audit_staff_user_id

    assert "username_changed" in action_map
    assert action_map["username_changed"]["actor_user_id"] == audit_student_id
    assert action_map["username_changed"]["target_user_id"] == audit_student_id

    assert "pin_changed" in action_map
    assert action_map["pin_changed"]["actor_user_id"] == audit_student_id
    assert action_map["pin_changed"]["target_user_id"] == audit_student_id

    assert "account_deleted" in action_map
    assert action_map["account_deleted"]["actor_user_id"] == admin_id
    assert action_map["account_deleted"]["target_user_id"] == audit_staff_user_id

    assert "account_recovered" in action_map
    assert action_map["account_recovered"]["actor_user_id"] == admin_id
    assert action_map["account_recovered"]["target_user_id"] == audit_staff_user_id
