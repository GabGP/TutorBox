"""GET /api/v1/presence/class: the teacher's lobby, with the status of each student."""

import sqlite3

from fastapi.testclient import TestClient

from tests.api.presence.presence_support import FakeClock
from tests.api.session.fleet_support import Clicker, StudentAccount, provision_clicker
from tests.conftest import auth_headers, get_user_id

CLASS_URL = "/api/v1/presence/class"
HEARTBEAT_URL = "/api/v1/presence/heartbeat"
DEVICE_ID = "ESP32-A4CF12"
CLICKER_SCOPE_DETAIL = "Clicker sessions can only vote."
ABSENT_PHONE = {"status": "absent", "seconds_ago": None}


def provision_for(
    client: TestClient,
    conn: sqlite3.Connection,
    username: str,
    device_id: str = DEVICE_ID,
) -> Clicker:
    return provision_clicker(
        client,
        auth_headers(client, "teacher1"),
        StudentAccount(student_id=get_user_id(conn, username), username=username),
        device_id,
    )


def read_class(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.get(CLASS_URL, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def teacher_read(client: TestClient) -> dict:
    return read_class(client, auth_headers(client, "teacher1"))


def row_of(body: dict, username: str) -> dict:
    return next(row for row in body["students"] if row["username"] == username)


def test_the_class_view_needs_a_session(staff_db, client, presence_store):
    assert client.get(CLASS_URL).status_code == 401


def test_a_student_cannot_read_the_class_view(
    staff_db, client, presence_store, student_headers
):
    response = client.get(CLASS_URL, headers=student_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions."


def test_a_clicker_token_cannot_read_the_class_view(staff_db, client, presence_store):
    _, conn = staff_db
    clicker = provision_for(client, conn, "student1")

    response = client.get(CLASS_URL, headers=clicker.headers)

    assert response.status_code == 403
    assert response.json()["detail"] == CLICKER_SCOPE_DETAIL


def test_a_student_who_never_connected_is_listed_as_absent(
    staff_db, client, presence_store
):
    _, conn = staff_db

    body = teacher_read(client)

    assert body == {
        "online": 0,
        "total": 2,
        "students": [
            {
                "user_id": get_user_id(conn, "student1"),
                "username": "student1",
                "status": "absent",
                "phone": ABSENT_PHONE,
                "clicker": None,
            },
            {
                "user_id": get_user_id(conn, "student2"),
                "username": "student2",
                "status": "absent",
                "phone": ABSENT_PHONE,
                "clicker": None,
            },
        ],
        "unassigned_clickers": [],
    }


def test_a_deleted_student_is_not_listed(staff_db, client, presence_store):
    _, conn = staff_db
    conn.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE username = 'student2'"
    )
    conn.commit()

    body = teacher_read(client)

    assert [row["username"] for row in body["students"]] == ["student1"]
    assert body["total"] == 1


def test_a_phone_only_student_is_online_on_the_phone(staff_db, client, presence_store):
    client.post(HEARTBEAT_URL, headers=auth_headers(client, "student1"))

    body = teacher_read(client)

    row = row_of(body, "student1")
    assert row["phone"] == {"status": "online", "seconds_ago": 0}
    assert row["clicker"] is None
    assert row["status"] == "online"
    assert body["online"] == 1


def test_a_clicker_only_student_shows_the_clicker_with_its_vitals(
    staff_db, client, presence_store
):
    _, conn = staff_db
    clicker = provision_for(client, conn, "student1")
    client.post(
        HEARTBEAT_URL, json={"rssi": -58, "battery_pct": 88}, headers=clicker.headers
    )

    row = row_of(teacher_read(client), "student1")

    assert row["status"] == "online"
    assert row["phone"] == ABSENT_PHONE
    assert row["clicker"] == {
        "device_id": DEVICE_ID,
        "status": "online",
        "seconds_ago": 0,
        "signal": "good",
        "rssi": -58,
        "battery_pct": 88,
    }


def test_a_clicker_never_heard_from_reports_no_vitals(staff_db, client, presence_store):
    _, conn = staff_db
    provision_for(client, conn, "student1")

    row = row_of(teacher_read(client), "student1")

    assert row["status"] == "absent"
    assert row["clicker"] == {
        "device_id": DEVICE_ID,
        "status": "absent",
        "seconds_ago": None,
        "signal": None,
        "rssi": None,
        "battery_pct": None,
    }


def test_a_clicker_that_stopped_is_dropped_and_keeps_its_last_vitals(
    staff_db, client, presence_store, presence_clock: FakeClock
):
    _, conn = staff_db
    clicker = provision_for(client, conn, "student1")
    client.post(
        HEARTBEAT_URL, json={"rssi": -80, "battery_pct": 40}, headers=clicker.headers
    )
    presence_clock.advance(16)

    row = row_of(teacher_read(client), "student1")

    assert row["status"] == "dropped"
    assert row["phone"] == ABSENT_PHONE
    assert row["clicker"] == {
        "device_id": DEVICE_ID,
        "status": "dropped",
        "seconds_ago": 16,
        "signal": "weak",
        "rssi": -80,
        "battery_pct": 40,
    }


def test_the_student_status_is_the_better_of_phone_and_clicker(
    staff_db, client, presence_store, presence_clock: FakeClock
):
    _, conn = staff_db
    clicker = provision_for(client, conn, "student1")
    client.post(HEARTBEAT_URL, json={"rssi": -70}, headers=clicker.headers)
    presence_clock.advance(16)
    client.post(HEARTBEAT_URL, headers=auth_headers(client, "student1"))

    row = row_of(teacher_read(client), "student1")

    assert row["phone"]["status"] == "online"
    assert row["clicker"]["status"] == "dropped"
    assert row["status"] == "online"


def test_unassigned_clickers_are_listed_by_id(staff_db, client, presence_store):
    _, conn = staff_db
    student2 = get_user_id(conn, "student2")
    conn.execute("INSERT INTO devices (device_id) VALUES ('ESP32-B7C001')")
    conn.execute(
        "INSERT INTO devices (device_id, assigned_user_id) VALUES ('ESP32-C00002', ?)",
        (student2,),
    )
    conn.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?", (student2,)
    )
    conn.commit()

    body = teacher_read(client)

    assert body["unassigned_clickers"] == ["ESP32-B7C001", "ESP32-C00002"]
    assert [row["username"] for row in body["students"]] == ["student1"]


def test_online_counts_only_the_students_whose_status_is_online(
    staff_db,
    client,
    presence_store,
    presence_clock: FakeClock,
):
    _, conn = staff_db
    conn.execute(
        "INSERT INTO users (username, hashed_pin, role) VALUES ('student3', "
        "'unused-pin-hash', 'student')"
    )
    conn.commit()
    clicker = provision_for(client, conn, "student2")
    client.post(HEARTBEAT_URL, json={"rssi": -70}, headers=clicker.headers)
    presence_clock.advance(16)
    client.post(HEARTBEAT_URL, headers=auth_headers(client, "student1"))

    body = teacher_read(client)

    assert body["total"] == 3
    assert body["online"] == 1
    assert row_of(body, "student2")["status"] == "dropped"
    assert row_of(body, "student3")["status"] == "absent"
