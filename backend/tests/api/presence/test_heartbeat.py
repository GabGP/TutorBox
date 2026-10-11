"""POST /api/v1/presence/heartbeat: what is recorded, and for whom."""

import logging
import sqlite3

import pytest
from fastapi.testclient import TestClient

from api.presence.store import Sighting
from tests.api.session.fleet_support import (
    Clicker,
    StudentAccount,
    provision_clicker,
)
from tests.conftest import auth_headers, get_user_id

HEARTBEAT_URL = "/api/v1/presence/heartbeat"
DEVICE_ID = "ESP32-A4CF12"


def provision_student1_clicker(client: TestClient, conn: sqlite3.Connection) -> Clicker:
    """Registers, assigns and logs in a clicker for student1, through the real endpoints."""
    return provision_clicker(
        client,
        auth_headers(client, "teacher1"),
        StudentAccount(student_id=get_user_id(conn, "student1"), username="student1"),
        DEVICE_ID,
    )


def test_the_heartbeat_needs_a_session(staff_db, client, presence_store):
    _, conn = staff_db
    assert client.post(HEARTBEAT_URL).status_code == 401

    response = client.post(
        HEARTBEAT_URL, headers={"Authorization": "Bearer not-a-token"}
    )

    assert response.status_code == 401
    assert presence_store.phone(get_user_id(conn, "student1")) is None


def test_a_student_phone_beats_without_a_body(staff_db, client, presence_store):
    _, conn = staff_db
    headers = auth_headers(client, "student1")

    response = client.post(HEARTBEAT_URL, headers=headers)

    assert response.status_code == 204
    assert response.content == b""
    assert presence_store.phone(get_user_id(conn, "student1")) == Sighting(
        seconds_ago=0
    )


def test_a_clicker_beat_is_stored_under_its_device_id_with_its_vitals(
    staff_db, client, presence_store, caplog
):
    _, conn = staff_db
    clicker = provision_student1_clicker(client, conn)

    with caplog.at_level(logging.DEBUG):
        response = client.post(
            HEARTBEAT_URL,
            json={"rssi": -58, "battery_pct": 88},
            headers=clicker.headers,
        )

    assert response.status_code == 204
    assert presence_store.clicker(DEVICE_ID) == Sighting(
        seconds_ago=0, rssi=-58, battery_pct=88
    )
    assert presence_store.phone(clicker.student_id) is None
    token = clicker.headers["Authorization"].removeprefix("Bearer ")
    assert token not in caplog.text


def test_a_clicker_beat_without_a_body_replaces_the_vitals_of_the_last(
    staff_db, client, presence_store
):
    _, conn = staff_db
    clicker = provision_student1_clicker(client, conn)
    client.post(
        HEARTBEAT_URL, json={"rssi": -58, "battery_pct": 88}, headers=clicker.headers
    )

    response = client.post(HEARTBEAT_URL, headers=clicker.headers)

    assert response.status_code == 204
    assert presence_store.clicker(DEVICE_ID) == Sighting(seconds_ago=0)


def test_vitals_sent_by_a_phone_are_ignored(staff_db, client, presence_store):
    _, conn = staff_db
    headers = auth_headers(client, "student1")

    response = client.post(
        HEARTBEAT_URL, json={"rssi": -40, "battery_pct": 5}, headers=headers
    )

    assert response.status_code == 204
    assert presence_store.phone(get_user_id(conn, "student1")) == Sighting(
        seconds_ago=0
    )


@pytest.mark.parametrize(
    "body",
    [
        {"rssi": 5},
        {"rssi": -121},
        {"battery_pct": 101},
        {"battery_pct": -1},
    ],
)
def test_out_of_range_vitals_answer_422_and_record_nothing(
    staff_db, client, presence_store, body
):
    _, conn = staff_db
    clicker = provision_student1_clicker(client, conn)

    response = client.post(HEARTBEAT_URL, json=body, headers=clicker.headers)

    assert response.status_code == 422
    assert presence_store.clicker(DEVICE_ID) is None


@pytest.mark.parametrize("username", ["teacher1", "admin1"])
def test_a_staff_heartbeat_is_accepted_and_recorded_nowhere(
    staff_db, client, presence_store, username
):
    _, conn = staff_db
    headers = auth_headers(client, username)

    response = client.post(HEARTBEAT_URL, json={"rssi": -40}, headers=headers)

    assert response.status_code == 204
    assert presence_store.phone(get_user_id(conn, username)) is None
    assert presence_store.clicker(DEVICE_ID) is None
