"""Tests for PATCH /api/v1/staff/users/{id}/role."""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def _user_id(conn, username: str) -> int:
    row = conn.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    return int(row["id"])


def _role(conn, username: str) -> str:
    row = conn.execute(
        "SELECT role FROM users WHERE username = ?", (username,)
    ).fetchone()
    return str(row["role"])


def test_teacher_promotes_student_to_teacher(staff_db, client: TestClient):
    """Teachers may move users between student and teacher roles."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1", "1234")
    sid = _user_id(conn, "student1")

    res = client.patch(
        f"/api/v1/staff/users/{sid}/role",
        headers=teacher_headers,
        json={"role": "teacher"},
    )
    assert res.status_code == 200
    assert res.json() == {"username": "student1", "role": "teacher"}
    assert _role(conn, "student1") == "teacher"

    audit_cursor = conn.execute(
        "SELECT * FROM audit_logs WHERE action = 'role_changed'"
    )
    assert audit_cursor.fetchone() is not None


def test_teacher_cannot_touch_admin_roles(staff_db, client: TestClient):
    """Teachers get 403 when assigning or modifying admin accounts."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1", "1234")
    sid = _user_id(conn, "student1")
    aid = _user_id(conn, "admin1")

    res_make_admin = client.patch(
        f"/api/v1/staff/users/{sid}/role",
        headers=teacher_headers,
        json={"role": "admin"},
    )
    assert res_make_admin.status_code == 403

    res_demote_admin = client.patch(
        f"/api/v1/staff/users/{aid}/role",
        headers=teacher_headers,
        json={"role": "teacher"},
    )
    assert res_demote_admin.status_code == 403
    assert _role(conn, "admin1") == "admin"


def test_admin_can_assign_any_role_but_not_last_admin(staff_db, client: TestClient):
    """Admins manage all roles; demoting the final admin is rejected."""
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1", "1234")
    sid = _user_id(conn, "student1")
    aid = _user_id(conn, "admin1")

    res_last = client.patch(
        f"/api/v1/staff/users/{aid}/role",
        headers=admin_headers,
        json={"role": "teacher"},
    )
    assert res_last.status_code == 409
    assert _role(conn, "admin1") == "admin"

    res = client.patch(
        f"/api/v1/staff/users/{sid}/role",
        headers=admin_headers,
        json={"role": "admin"},
    )
    assert res.status_code == 200
    assert _role(conn, "student1") == "admin"

    res_ok = client.patch(
        f"/api/v1/staff/users/{aid}/role",
        headers=admin_headers,
        json={"role": "teacher"},
    )
    assert res_ok.status_code == 200
    assert _role(conn, "admin1") == "teacher"


def test_change_role_not_found_and_rbac(staff_db, client: TestClient):
    """Unknown users 404; students 403."""
    teacher_headers = auth_headers(client, "teacher1", "1234")
    student_headers = auth_headers(client, "student1", "1234")

    res_missing = client.patch(
        "/api/v1/staff/users/999999/role",
        headers=teacher_headers,
        json={"role": "teacher"},
    )
    assert res_missing.status_code == 404

    res_student = client.patch(
        "/api/v1/staff/users/1/role",
        headers=student_headers,
        json={"role": "teacher"},
    )
    assert res_student.status_code == 403


def test_cannot_demote_last_teacher(staff_db, client: TestClient):
    """Demoting the final teacher is rejected, then allowed once backed up."""
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1", "1234")
    tid = _user_id(conn, "teacher1")
    sid = _user_id(conn, "student1")

    res_last = client.patch(
        f"/api/v1/staff/users/{tid}/role",
        headers=admin_headers,
        json={"role": "student"},
    )
    assert res_last.status_code == 409
    assert _role(conn, "teacher1") == "teacher"

    # Promote a backup teacher first, then the demote succeeds.
    res_promote = client.patch(
        f"/api/v1/staff/users/{sid}/role",
        headers=admin_headers,
        json={"role": "teacher"},
    )
    assert res_promote.status_code == 200

    res_ok = client.patch(
        f"/api/v1/staff/users/{tid}/role",
        headers=admin_headers,
        json={"role": "student"},
    )
    assert res_ok.status_code == 200
    assert _role(conn, "teacher1") == "student"


def test_change_role_noop_same_role(staff_db, client: TestClient):
    """Patching user with their existing role is a 200 no-op."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1", "1234")
    sid = _user_id(conn, "student1")

    res = client.patch(
        f"/api/v1/staff/users/{sid}/role",
        headers=teacher_headers,
        json={"role": "student"},
    )
    assert res.status_code == 200
    assert res.json() == {"username": "student1", "role": "student"}


def test_cannot_demote_when_last_manager_remains(staff_db, client: TestClient):
    """Demoting to student when only one manager exists triggers 409 lockout guard."""
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1", "1234")
    # Soft delete teacher1 so admin1 is the sole remaining staff manager
    conn.execute(
        "UPDATE users SET deleted_at = '2026-01-01' WHERE username = 'teacher1'"
    )
    conn.commit()

    aid = _user_id(conn, "admin1")
    res = client.patch(
        f"/api/v1/staff/users/{aid}/role",
        headers=admin_headers,
        json={"role": "student"},
    )
    assert res.status_code == 409


def test_ensure_managers_remain_direct(staff_db):
    """ensure_managers_remain raises 409 when <= 1 live manager exists."""
    import pytest
    from fastapi import HTTPException

    from api.staff.guards import ensure_managers_remain

    _, conn = staff_db
    conn.execute(
        "UPDATE users SET deleted_at = '2026-01-01' WHERE username = 'teacher1'"
    )
    conn.commit()
    with pytest.raises(HTTPException) as exc_info:
        ensure_managers_remain(conn, "teacher", verb="delete")
    assert exc_info.value.status_code == 409
