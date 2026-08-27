import logging

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, get_user_id


def test_teacher_resets_student_pin(staff_db, client: TestClient):
    """
    Teacher can reset a student's PIN.
    Returns 200 OK with a 6-digit temporary PIN.
    The database flags must_change_pin=1, old PIN fails, and temp PIN succeeds.
    """
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    res = client.post(f"/users/{student_id}/reset-pin", headers=teacher_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "student1"
    temp_pin = data["temporary_pin"]
    assert len(temp_pin) == 6
    assert temp_pin.isdigit()

    # Verify must_change_pin in DB
    cursor = conn.cursor()
    cursor.execute("SELECT must_change_pin FROM users WHERE id = ?", (student_id,))
    assert cursor.fetchone()["must_change_pin"] == 1

    # Old PIN must fail
    old_login = client.post("/login", json={"username": "student1", "pin": "1234"})
    assert old_login.status_code == 401

    # Temp PIN must succeed and indicate must_change_pin=True
    new_login = client.post("/login", json={"username": "student1", "pin": temp_pin})
    assert new_login.status_code == 200
    assert new_login.json()["must_change_pin"] is True


def test_teacher_resets_target_invalidates_all_target_sessions(
    staff_db, client: TestClient
):
    """
    Resetting a user's PIN immediately invalidates all active sessions for that user.
    """
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")

    # Student logs in
    login_res = client.post("/login", json={"username": "student1", "pin": "1234"})
    student_token = login_res.json()["session_id"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Verify student session works
    me_res = client.get("/users/me", headers=student_headers)
    assert me_res.status_code == 200

    # Teacher resets student PIN
    teacher_headers = auth_headers(client, "teacher1", "1234")
    reset_res = client.post(f"/users/{student_id}/reset-pin", headers=teacher_headers)
    assert reset_res.status_code == 200

    # Student's prior session is now invalid (401 Unauthorized)
    me_after = client.get("/users/me", headers=student_headers)
    assert me_after.status_code == 401


def test_teacher_resetting_admin_returns_403(staff_db, client: TestClient):
    """
    A teacher cannot reset an admin's PIN (403 Forbidden).
    """
    _, conn = staff_db
    admin_id = get_user_id(conn, "admin1")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    res = client.post(f"/users/{admin_id}/reset-pin", headers=teacher_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Only admins may reset admin PINs."


def test_teacher_resets_another_teacher(staff_db, client: TestClient):
    """
    Under the uniform staff matrix, a teacher CAN reset another teacher's PIN.
    """
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Create teacher2
    create_res = client.post(
        "/users",
        headers=teacher_headers,
        json={"username": "teacher2", "pin": "1234", "role": "teacher"},
    )
    assert create_res.status_code == 201
    teacher2_id = get_user_id(conn, "teacher2")

    reset_res = client.post(f"/users/{teacher2_id}/reset-pin", headers=teacher_headers)
    assert reset_res.status_code == 200
    assert reset_res.json()["username"] == "teacher2"
    assert len(reset_res.json()["temporary_pin"]) == 6


def test_admin_resets_any_account(staff_db, client: TestClient):
    """
    An admin can reset any account: student, teacher, or another admin.
    """
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1", "1234")

    # Admin resets student
    student_id = get_user_id(conn, "student1")
    res_s = client.post(f"/users/{student_id}/reset-pin", headers=admin_headers)
    assert res_s.status_code == 200

    # Admin resets teacher
    teacher_id = get_user_id(conn, "teacher1")
    res_t = client.post(f"/users/{teacher_id}/reset-pin", headers=admin_headers)
    assert res_t.status_code == 200

    # Admin creates and resets another admin
    client.post(
        "/users",
        headers=admin_headers,
        json={"username": "admin2", "pin": "1234", "role": "admin"},
    )
    admin2_id = get_user_id(conn, "admin2")
    res_a = client.post(f"/users/{admin2_id}/reset-pin", headers=admin_headers)
    assert res_a.status_code == 200


def test_reset_pin_target_not_found(staff_db, client: TestClient):
    """
    Resetting a non-existent user returns 404 Not Found.
    """
    admin_headers = auth_headers(client, "admin1", "1234")
    res = client.post("/users/99999/reset-pin", headers=admin_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found."


def test_reset_pin_target_soft_deleted(staff_db, client: TestClient):
    """
    Resetting a soft-deleted user returns 404 Not Found.
    """
    _, conn = staff_db
    student2_id = get_user_id(conn, "student2")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
        (student2_id,),
    )
    conn.commit()

    admin_headers = auth_headers(client, "admin1", "1234")
    res = client.post(f"/users/{student2_id}/reset-pin", headers=admin_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "User not found."


def test_reset_pin_forbidden_for_students(staff_db, client: TestClient):
    """
    Student role is forbidden (403) from resetting PINs.
    """
    _, conn = staff_db
    student2_id = get_user_id(conn, "student2")
    student_headers = auth_headers(client, "student1", "1234")

    res = client.post(f"/users/{student2_id}/reset-pin", headers=student_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "Insufficient permissions."


def test_reset_pin_unauthenticated(client: TestClient):
    """
    Unauthenticated caller receives 401 Unauthorized.
    """
    res = client.post("/users/1/reset-pin")
    assert res.status_code == 401


def test_reset_pin_blocked_during_pending_rotation(temp_db, client: TestClient):
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

    res = client.post(f"/users/{target_id}/reset-pin", headers=headers)
    assert res.status_code == 403
    assert res.json()["detail"] == "PIN change required."


def test_reset_pin_temporary_pin_never_logged(staff_db, client: TestClient, caplog):
    """
    SECURITY PROOF:
    The temporary PIN generated for a reset must never appear in any log output.
    """
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    teacher_headers = auth_headers(client, "teacher1", "1234")

    with caplog.at_level(logging.DEBUG):
        res = client.post(f"/users/{student_id}/reset-pin", headers=teacher_headers)

    assert res.status_code == 200
    temp_pin = res.json()["temporary_pin"]

    for record in caplog.records:
        assert temp_pin not in record.getMessage(), (
            f"Security violation: Temporary PIN leaked in log message: '{record.getMessage()}'"
        )
