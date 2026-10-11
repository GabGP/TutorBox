import gc
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, get_user_id

SHORT_BUSY_TIMEOUT_MS = "200"
DEVICES_URL = "/api/v1/staff/devices"
STAFF_USERS_URL = "/api/v1/staff/users"
SIGNUP_URL = "/api/v1/users/signup"
LOGIN_URL = "/api/v1/auth/login"


@pytest.fixture(autouse=True)
def short_busy_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """A write that meets a held lock fails after 0.2 s instead of the default 5 s."""
    monkeypatch.setenv("DB_BUSY_TIMEOUT_MS", SHORT_BUSY_TIMEOUT_MS)


@pytest.fixture(autouse=True)
def no_cycle_collection() -> Iterator[None]:
    """
    The refused request leaves its cursor in a reference cycle with the raised error.
    With the collector off the cursor stays alive, as it does on the appliance until
    the next collection, so these tests do not depend on when a collection happens.
    """
    gc.collect()
    gc.disable()
    yield
    gc.enable()


def assert_next_write_is_accepted(client: TestClient) -> None:
    """Logging in stores a session, so it fails while another connection holds the lock."""
    response = client.post(LOGIN_URL, json={"username": "student1", "pin": "1234"})
    assert response.status_code == 200


def test_write_is_accepted_after_a_duplicate_clicker_id(staff_db, client):
    """Registering a clicker id twice answers 409 and leaves the database unlocked."""
    headers = auth_headers(client, "teacher1")
    clicker = {"device_id": "ESP32-A4CF12"}
    assert client.post(DEVICES_URL, json=clicker, headers=headers).status_code == 201

    duplicate = client.post(DEVICES_URL, json=clicker, headers=headers)

    assert duplicate.status_code == 409
    other_clicker = {"device_id": "ESP32-B7C001"}
    assert (
        client.post(DEVICES_URL, json=other_clicker, headers=headers).status_code == 201
    )
    assert_next_write_is_accepted(client)


def test_write_is_accepted_after_a_duplicate_staff_created_username(staff_db, client):
    """Creating a user with a taken username answers 409 and leaves the database unlocked."""
    headers = auth_headers(client, "teacher1")
    taken = {"username": "student1", "pin": "1234", "role": "student"}

    duplicate = client.post(STAFF_USERS_URL, json=taken, headers=headers)

    assert duplicate.status_code == 409
    assert_next_write_is_accepted(client)


def test_write_is_accepted_after_a_duplicate_signup(staff_db, client):
    """Signing up with a taken username answers 409 and leaves the database unlocked."""
    duplicate = client.post(SIGNUP_URL, json={"username": "student1", "pin": "5678"})

    assert duplicate.status_code == 409
    assert_next_write_is_accepted(client)


def test_write_is_accepted_after_a_duplicate_username_change(staff_db, client):
    """Changing to a taken username answers 409 and leaves the database unlocked."""
    headers = auth_headers(client, "student2")

    duplicate = client.patch(
        "/api/v1/users/me/username",
        headers=headers,
        json={"current_pin": "1234", "new_username": "student1"},
    )

    assert duplicate.status_code == 409
    assert_next_write_is_accepted(client)


def test_write_is_accepted_after_a_duplicate_username_on_recover(staff_db, client):
    """Recovering an account under a taken username answers 409 and leaves the database unlocked."""
    _, conn = staff_db
    student2_id = get_user_id(conn, "student2")
    headers = auth_headers(client, "teacher1")
    assert (
        client.delete(f"{STAFF_USERS_URL}/{student2_id}", headers=headers).status_code
        == 200
    )

    duplicate = client.post(
        f"{STAFF_USERS_URL}/{student2_id}/recover",
        headers=headers,
        json={"username": "student1"},
    )

    assert duplicate.status_code == 409
    assert_next_write_is_accepted(client)
