import logging
import re
import uuid

from fastapi.testclient import TestClient

from core.db.device_repository import create_device_session
from core.security import token_digest
from tests.api.clicker_support import clicker_token_is_live
from tests.conftest import auth_headers, get_user_id

CLICKER_ID = "ESP32-A4CF12"
SECRET_URL = f"/api/v1/staff/devices/{CLICKER_ID}/secret"
ME_URL = "/api/v1/users/me"
SECRET_SHAPE = re.compile(r"[0-9a-f]{32}")


def register_clicker(client: TestClient, headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/staff/devices", json={"device_id": CLICKER_ID}, headers=headers
    )
    assert response.status_code == 201


def assign_clicker(client: TestClient, headers: dict[str, str], user_id: int) -> None:
    response = client.post(
        f"/api/v1/staff/devices/{CLICKER_ID}/assign",
        json={"user_id": user_id},
        headers=headers,
    )
    assert response.status_code == 200


def issue_clicker_token(conn, user_id: int) -> dict[str, str]:
    """Stores a device session the way the clicker's token exchange will."""
    token = str(uuid.uuid4())
    create_device_session(conn, token_digest(token), user_id, CLICKER_ID)
    conn.commit()
    return {"Authorization": f"Bearer {token}"}


def me_status(client: TestClient, headers: dict[str, str]) -> int:
    return client.get(ME_URL, headers=headers).status_code


def read_clicker_secret_columns(conn):
    return conn.execute(
        "SELECT secret_hash, secret_issued_at FROM devices WHERE device_id = ?",
        (CLICKER_ID,),
    ).fetchone()


def read_latest_secret_audit_row(conn):
    return conn.execute(
        "SELECT actor_user_id, target_user_id FROM audit_logs "
        "WHERE action = 'device_secret_issued' ORDER BY id DESC LIMIT 1"
    ).fetchone()


def test_teacher_gets_200_with_device_id_and_secret_only(staff_db, client):
    """A teacher gets the secret as a 32-character lowercase hex string."""
    headers = auth_headers(client, "teacher1")
    register_clicker(client, headers)

    response = client.post(SECRET_URL, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"device_id", "secret"}
    assert body["device_id"] == CLICKER_ID
    assert SECRET_SHAPE.fullmatch(body["secret"])


def test_admin_can_issue_secret(staff_db, client):
    """An admin is allowed to issue a clicker secret, like a teacher."""
    headers = auth_headers(client, "admin1")
    register_clicker(client, headers)

    response = client.post(SECRET_URL, headers=headers)

    assert response.status_code == 200


def test_student_gets_403_and_no_secret_is_stored(staff_db, client):
    """A student is refused and the clicker keeps no secret."""
    _, conn = staff_db
    register_clicker(client, auth_headers(client, "teacher1"))
    student_headers = auth_headers(client, "student1")

    response = client.post(SECRET_URL, headers=student_headers)

    assert response.status_code == 403
    assert read_clicker_secret_columns(conn)["secret_hash"] is None


def test_request_without_token_gets_401(staff_db, client):
    """A request with no bearer token is refused before any lookup."""
    register_clicker(client, auth_headers(client, "teacher1"))

    response = client.post(SECRET_URL)

    assert response.status_code == 401


def test_unknown_device_gets_404(staff_db, client):
    """A clicker that was never registered has no secret to issue."""
    headers = auth_headers(client, "teacher1")

    response = client.post(
        "/api/v1/staff/devices/NO-SUCH-CLICKER/secret", headers=headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found."


def test_database_keeps_digest_of_secret_not_the_secret(staff_db, client):
    """The clicker row stores the digest of the secret and when it was issued."""
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    register_clicker(client, headers)

    secret = client.post(SECRET_URL, headers=headers).json()["secret"]

    stored = read_clicker_secret_columns(conn)
    assert stored["secret_hash"] == token_digest(secret)
    assert stored["secret_hash"] != secret
    assert stored["secret_issued_at"] is not None


def test_second_issue_replaces_first_secret(staff_db, client):
    """Issuing twice returns two different secrets; only the second is kept."""
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    register_clicker(client, headers)

    first_secret = client.post(SECRET_URL, headers=headers).json()["secret"]
    second_secret = client.post(SECRET_URL, headers=headers).json()["secret"]

    assert first_secret != second_secret
    stored = read_clicker_secret_columns(conn)
    assert stored["secret_hash"] == token_digest(second_secret)


def test_audit_row_names_teacher_actor_and_assigned_student_target(staff_db, client):
    """The audit trail records who issued the secret and for which student."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    teacher_id = get_user_id(conn, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers)
    assign_clicker(client, teacher_headers, student_id)

    assert client.post(SECRET_URL, headers=teacher_headers).status_code == 200

    audit_row = read_latest_secret_audit_row(conn)
    assert audit_row["actor_user_id"] == teacher_id
    assert audit_row["target_user_id"] == student_id


def test_audit_row_has_no_target_for_unassigned_clicker(staff_db, client):
    """An unassigned clicker's audit row has a NULL target."""
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    register_clicker(client, headers)

    assert client.post(SECRET_URL, headers=headers).status_code == 200

    audit_row = read_latest_secret_audit_row(conn)
    assert audit_row["target_user_id"] is None


def test_issuing_secret_revokes_clicker_token_but_keeps_phone_login(staff_db, client):
    """The old clicker token stops working; the student's phone login does not."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1")
    student_id = get_user_id(conn, "student1")
    register_clicker(client, teacher_headers)
    assign_clicker(client, teacher_headers, student_id)
    clicker_headers = issue_clicker_token(conn, student_id)
    phone_headers = auth_headers(client, "student1")
    assert clicker_token_is_live(client, clicker_headers)

    assert client.post(SECRET_URL, headers=teacher_headers).status_code == 200

    assert not clicker_token_is_live(client, clicker_headers)
    assert me_status(client, phone_headers) == 200


def test_unassigned_clicker_can_be_issued_a_secret(staff_db, client):
    """Issuing does not require the clicker to be assigned to a student."""
    headers = auth_headers(client, "teacher1")
    register_clicker(client, headers)

    response = client.post(SECRET_URL, headers=headers)

    assert response.status_code == 200


def test_issued_secret_and_its_digest_never_reach_the_log(staff_db, client, caplog):
    """The log names the clicker but never the secret or its digest."""
    headers = auth_headers(client, "teacher1")
    register_clicker(client, headers)

    with caplog.at_level(logging.DEBUG):
        response = client.post(SECRET_URL, headers=headers)

    secret = response.json()["secret"]
    assert response.status_code == 200
    assert CLICKER_ID in caplog.text
    assert secret not in caplog.text
    assert token_digest(secret) not in caplog.text
