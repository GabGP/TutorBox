"""PATCH /api/v1/staff/users/{id}/role: a clicker is held by students only.

An account that stops being a student gives its clicker back, and the token that
clicker was issued stops working.
"""

import pytest
from fastapi.testclient import TestClient

from tests.api.clicker_support import clicker_token_is_live
from tests.api.staff.test_device_revocation import (
    CLICKER_A,
    CLICKER_B,
    assign_clicker,
    issue_clicker_token,
    register_clicker,
)
from tests.conftest import auth_headers, get_user_id

SECRET = "0123456789abcdef0123456789abcdef"


def change_role(
    client: TestClient, headers: dict[str, str], user_id: int, role: str
) -> None:
    response = client.patch(
        f"/api/v1/staff/users/{user_id}/role", json={"role": role}, headers=headers
    )
    assert response.status_code == 200, response.text


def assigned_user_id_of(
    client: TestClient, headers: dict[str, str], device_id: str
) -> int | None:
    devices = client.get("/api/v1/staff/devices", headers=headers).json()["devices"]
    return next(
        device["assigned_user_id"]
        for device in devices
        if device["device_id"] == device_id
    )


@pytest.mark.parametrize("new_role", ["teacher", "admin"])
def test_student_who_becomes_staff_gives_the_clicker_back(staff_db, client, new_role):
    _, conn = staff_db
    admin_headers = auth_headers(client, "admin1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, admin_headers, CLICKER_A)
    assign_clicker(client, admin_headers, CLICKER_A, student_id)

    change_role(client, admin_headers, student_id, new_role)

    assert assigned_user_id_of(client, admin_headers, CLICKER_A) is None


def test_student_who_becomes_teacher_loses_the_clickers_token(staff_db, client):
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers, CLICKER_A)
    assign_clicker(client, teacher_headers, CLICKER_A, student_id)
    clicker_headers = issue_clicker_token(conn, student_id, CLICKER_A)
    assert clicker_token_is_live(client, clicker_headers)

    change_role(client, teacher_headers, student_id, "teacher")

    assert not clicker_token_is_live(client, clicker_headers)


def test_clicker_of_a_new_teacher_cannot_authenticate_again(staff_db, client):
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers, CLICKER_A)
    assign_clicker(client, teacher_headers, CLICKER_A, student_id)
    first_contact = client.post(
        "/api/v1/devices/auth", json={"device_id": CLICKER_A, "secret": SECRET}
    )
    assert first_contact.status_code == 200, first_contact.text

    change_role(client, teacher_headers, student_id, "teacher")

    response = client.post(
        "/api/v1/devices/auth", json={"device_id": CLICKER_A, "secret": SECRET}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Device is not assigned to any student."


def test_new_teacher_keeps_the_phone_login(staff_db, client):
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers, CLICKER_A)
    assign_clicker(client, teacher_headers, CLICKER_A, student_id)
    phone_headers = auth_headers(client, "student1")

    change_role(client, teacher_headers, student_id, "teacher")

    profile = client.get("/api/v1/users/me", headers=phone_headers)
    assert profile.status_code == 200
    assert profile.json()["role"] == "teacher"


def test_another_students_clicker_is_left_alone(staff_db, client):
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    promoted_id = get_user_id(conn, "student1")
    other_id = get_user_id(conn, "student2")
    register_clicker(client, teacher_headers, CLICKER_A)
    register_clicker(client, teacher_headers, CLICKER_B)
    assign_clicker(client, teacher_headers, CLICKER_A, promoted_id)
    assign_clicker(client, teacher_headers, CLICKER_B, other_id)
    other_clicker_headers = issue_clicker_token(conn, other_id, CLICKER_B)

    change_role(client, teacher_headers, promoted_id, "teacher")

    assert assigned_user_id_of(client, teacher_headers, CLICKER_B) == other_id
    assert clicker_token_is_live(client, other_clicker_headers)


def test_role_change_to_the_same_role_keeps_the_clicker_and_its_token(staff_db, client):
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers, CLICKER_A)
    assign_clicker(client, teacher_headers, CLICKER_A, student_id)
    clicker_headers = issue_clicker_token(conn, student_id, CLICKER_A)

    change_role(client, teacher_headers, student_id, "student")

    assert assigned_user_id_of(client, teacher_headers, CLICKER_A) == student_id
    assert clicker_token_is_live(client, clicker_headers)


def test_clicker_given_back_is_audited_as_unassigned(staff_db, client):
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers, CLICKER_A)
    assign_clicker(client, teacher_headers, CLICKER_A, student_id)

    change_role(client, teacher_headers, student_id, "teacher")

    unassigned_rows = conn.execute(
        "SELECT actor_user_id, target_user_id FROM audit_logs "
        "WHERE action = 'device_unassigned'"
    ).fetchall()
    assert [tuple(row) for row in unassigned_rows] == [
        (get_user_id(conn, "teacher1"), student_id)
    ]


def test_student_without_a_clicker_is_promoted_with_no_unassign_audit(staff_db, client):
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")

    change_role(client, teacher_headers, student_id, "teacher")

    unassigned_count = conn.execute(
        "SELECT COUNT(*) FROM audit_logs WHERE action = 'device_unassigned'"
    ).fetchone()[0]
    assert unassigned_count == 0
