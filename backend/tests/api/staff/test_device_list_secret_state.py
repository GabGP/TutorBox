import re

from fastapi.testclient import TestClient

from core.security import token_digest
from tests.conftest import auth_headers

CLICKER_ID = "ESP32-A4CF12"
DEVICES_URL = "/api/v1/staff/devices"
SECRET_URL = f"{DEVICES_URL}/{CLICKER_ID}/secret"
TIMESTAMP_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
LISTED_FIELDS = {
    "device_id",
    "assigned_user_id",
    "assigned_username",
    "created_at",
    "secret_issued_at",
}


def register_clicker(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(DEVICES_URL, json={"device_id": CLICKER_ID}, headers=headers)
    assert response.status_code == 201
    return response.json()


def list_clicker(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.get(DEVICES_URL, headers=headers)
    assert response.status_code == 200
    (listed_clicker,) = response.json()["devices"]
    return listed_clicker


def test_listed_clicker_has_no_issue_time_before_a_secret_is_issued(staff_db, client):
    """A clicker that was only registered is listed with a null issue time."""
    headers = auth_headers(client, "teacher1")
    registered_clicker = register_clicker(client, headers)

    listed_clicker = list_clicker(client, headers)

    assert registered_clicker["secret_issued_at"] is None
    assert listed_clicker["secret_issued_at"] is None


def test_listed_clicker_shows_when_its_secret_was_issued(staff_db, client):
    """After a secret is issued the list carries the stored issue time."""
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    register_clicker(client, headers)
    assert client.post(SECRET_URL, headers=headers).status_code == 200

    listed_clicker = list_clicker(client, headers)

    stored_issue_time = conn.execute(
        "SELECT secret_issued_at FROM devices WHERE device_id = ?", (CLICKER_ID,)
    ).fetchone()["secret_issued_at"]
    assert TIMESTAMP_SHAPE.fullmatch(listed_clicker["secret_issued_at"])
    assert listed_clicker["secret_issued_at"] == stored_issue_time


def test_list_never_returns_the_secret_or_its_digest(staff_db, client):
    """The list names when a secret was issued, never the secret or its digest."""
    headers = auth_headers(client, "teacher1")
    register_clicker(client, headers)
    secret_response = client.post(SECRET_URL, headers=headers)
    assert secret_response.status_code == 200
    secret = secret_response.json()["secret"]

    response = client.get(DEVICES_URL, headers=headers)

    assert set(response.json()["devices"][0].keys()) == LISTED_FIELDS
    assert secret not in response.text
    assert token_digest(secret) not in response.text
