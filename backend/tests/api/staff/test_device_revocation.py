import uuid

from fastapi.testclient import TestClient

from core.db.device_repository import create_device_session
from core.security import token_digest
from tests.api.clicker_support import clicker_token_is_live
from tests.conftest import auth_headers, get_user_id

ME_URL = "/api/v1/users/me"
CLICKER_A = "ESP32-A4CF12"
CLICKER_B = "ESP32-B7D901"


def register_clicker(
    client: TestClient, headers: dict[str, str], device_id: str
) -> None:
    response = client.post(
        "/api/v1/staff/devices", json={"device_id": device_id}, headers=headers
    )
    assert response.status_code == 201


def assign_clicker(
    client: TestClient, headers: dict[str, str], device_id: str, user_id: int
) -> None:
    response = client.post(
        f"/api/v1/staff/devices/{device_id}/assign",
        json={"user_id": user_id},
        headers=headers,
    )
    assert response.status_code == 200


def issue_clicker_token(conn, user_id: int, device_id: str) -> dict[str, str]:
    """Stores a device session the way the clicker's token exchange will."""
    token = str(uuid.uuid4())
    create_device_session(conn, token_digest(token), user_id, device_id)
    conn.commit()
    return {"Authorization": f"Bearer {token}"}


def me_status(client: TestClient, headers: dict[str, str]) -> int:
    return client.get(ME_URL, headers=headers).status_code


def test_unassigning_clicker_revokes_its_token(staff_db, client):
    """Unassigning a clicker makes the token it was issued stop working."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers, CLICKER_A)
    assign_clicker(client, teacher_headers, CLICKER_A, student_id)
    clicker_headers = issue_clicker_token(conn, student_id, CLICKER_A)
    assert clicker_token_is_live(client, clicker_headers)

    response = client.post(
        f"/api/v1/staff/devices/{CLICKER_A}/unassign", headers=teacher_headers
    )

    assert response.status_code == 200
    assert not clicker_token_is_live(client, clicker_headers)


def test_unassigning_clicker_keeps_student_phone_login(staff_db, client):
    """The student's phone login survives the clicker being unassigned."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers, CLICKER_A)
    assign_clicker(client, teacher_headers, CLICKER_A, student_id)
    phone_headers = auth_headers(client, "student1")

    client.post(f"/api/v1/staff/devices/{CLICKER_A}/unassign", headers=teacher_headers)

    assert me_status(client, phone_headers) == 200


def test_assigning_clicker_to_another_student_revokes_previous_students_token(
    staff_db, client
):
    """A clicker handed to a new student drops the token of the previous one."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student1_id = get_user_id(conn, "student1")
    student2_id = get_user_id(conn, "student2")
    register_clicker(client, teacher_headers, CLICKER_A)
    assign_clicker(client, teacher_headers, CLICKER_A, student1_id)
    previous_holder_headers = issue_clicker_token(conn, student1_id, CLICKER_A)

    assign_clicker(client, teacher_headers, CLICKER_A, student2_id)

    assert not clicker_token_is_live(client, previous_holder_headers)


def test_moving_student_to_another_clicker_revokes_token_of_previous_clicker(
    staff_db, client
):
    """A student moved to clicker B loses the token of clicker A they held."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers, CLICKER_A)
    register_clicker(client, teacher_headers, CLICKER_B)
    assign_clicker(client, teacher_headers, CLICKER_A, student_id)
    old_clicker_headers = issue_clicker_token(conn, student_id, CLICKER_A)

    assign_clicker(client, teacher_headers, CLICKER_B, student_id)

    assert not clicker_token_is_live(client, old_clicker_headers)


def test_reassigning_same_student_to_same_clicker_keeps_token(staff_db, client):
    """Assigning a student to the clicker they already hold changes nothing."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers, CLICKER_A)
    assign_clicker(client, teacher_headers, CLICKER_A, student_id)
    clicker_headers = issue_clicker_token(conn, student_id, CLICKER_A)

    assign_clicker(client, teacher_headers, CLICKER_A, student_id)

    assert clicker_token_is_live(client, clicker_headers)


def test_deleting_clicker_revokes_its_token(staff_db, client):
    """Removing a clicker from the fleet makes its token stop working."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers, CLICKER_A)
    assign_clicker(client, teacher_headers, CLICKER_A, student_id)
    clicker_headers = issue_clicker_token(conn, student_id, CLICKER_A)

    response = client.delete(
        f"/api/v1/staff/devices/{CLICKER_A}", headers=teacher_headers
    )

    assert response.status_code == 200
    assert not clicker_token_is_live(client, clicker_headers)


def test_unassigning_one_clicker_keeps_another_clickers_token(staff_db, client):
    """Only the unassigned clicker's token is revoked; the other one still works."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student1_id = get_user_id(conn, "student1")
    student2_id = get_user_id(conn, "student2")
    register_clicker(client, teacher_headers, CLICKER_A)
    register_clicker(client, teacher_headers, CLICKER_B)
    assign_clicker(client, teacher_headers, CLICKER_A, student1_id)
    assign_clicker(client, teacher_headers, CLICKER_B, student2_id)
    unassigned_headers = issue_clicker_token(conn, student1_id, CLICKER_A)
    other_headers = issue_clicker_token(conn, student2_id, CLICKER_B)

    client.post(f"/api/v1/staff/devices/{CLICKER_A}/unassign", headers=teacher_headers)

    assert not clicker_token_is_live(client, unassigned_headers)
    assert clicker_token_is_live(client, other_headers)
