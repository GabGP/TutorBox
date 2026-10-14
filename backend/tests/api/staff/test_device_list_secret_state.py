"""GET /api/v1/staff/devices: the list shows when a clicker first made contact, never its secret."""

import re

from fastapi.testclient import TestClient

from core.security import token_digest
from tests.conftest import auth_headers

CLICKER_ID = "ESP32-A4CF12"
DEVICES_URL = "/api/v1/staff/devices"
AUTH_URL = "/api/v1/devices/auth"
SECRET = "0123456789abcdef0123456789abcdef"
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


def make_first_contact(client: TestClient) -> None:
    """The clicker logs in with its own secret, which enrolls it. It has no student, so 403."""
    response = client.post(AUTH_URL, json={"device_id": CLICKER_ID, "secret": SECRET})
    assert response.status_code == 403, response.text


def test_listed_clicker_has_no_issue_time_before_its_first_contact(staff_db, client):
    """A clicker that was only registered is listed with a null issue time."""
    headers = auth_headers(client, "teacher1")
    registered_clicker = register_clicker(client, headers)

    listed_clicker = list_clicker(client, headers)

    assert registered_clicker["secret_issued_at"] is None
    assert listed_clicker["secret_issued_at"] is None


def test_listed_clicker_shows_when_its_secret_was_first_stored(staff_db, client):
    """After the clicker's first contact the list carries the stored time."""
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    register_clicker(client, headers)
    make_first_contact(client)

    listed_clicker = list_clicker(client, headers)

    stored_issue_time = conn.execute(
        "SELECT secret_issued_at FROM devices WHERE device_id = ?", (CLICKER_ID,)
    ).fetchone()["secret_issued_at"]
    assert TIMESTAMP_SHAPE.fullmatch(listed_clicker["secret_issued_at"])
    assert listed_clicker["secret_issued_at"] == stored_issue_time


def test_self_enrolled_clicker_is_listed_with_its_first_contact_time(staff_db, client):
    """A clicker that was never registered by hand shows up after its first contact."""
    headers = auth_headers(client, "teacher1")
    make_first_contact(client)

    listed_clicker = list_clicker(client, headers)

    assert listed_clicker["device_id"] == CLICKER_ID
    assert TIMESTAMP_SHAPE.fullmatch(listed_clicker["secret_issued_at"])


def test_list_never_returns_the_secret_or_its_digest(staff_db, client):
    """The list names when a secret was stored, never the secret or its digest."""
    headers = auth_headers(client, "teacher1")
    register_clicker(client, headers)
    make_first_contact(client)

    response = client.get(DEVICES_URL, headers=headers)

    assert set(response.json()["devices"][0].keys()) == LISTED_FIELDS
    assert SECRET not in response.text
    assert token_digest(SECRET) not in response.text
