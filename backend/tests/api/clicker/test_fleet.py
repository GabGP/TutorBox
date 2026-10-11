"""The teacher's clicker list (GET /staff/devices) with enrollment and fleet health."""

from tests.api.clicker.helpers import (
    CLICKER_ID,
    OTHER_SECRET,
    assign,
    checkin,
)
from tests.conftest import auth_headers, get_user_id


def _devices(client, headers) -> dict[str, dict]:
    response = client.get("/api/v1/staff/devices", headers=headers)
    assert response.status_code == 200
    return {item["device_id"]: item for item in response.json()["devices"]}


def test_list_reports_enrollment_and_vitals(staff_db, client):
    teacher = auth_headers(client, "teacher1")
    client.post("/api/v1/staff/devices", json={"device_id": "spare"}, headers=teacher)
    checkin(client, firmware="1.0.0", rssi=-61, battery_mv=3870)

    devices = _devices(client, teacher)

    clicker = devices[CLICKER_ID]
    assert (clicker["enrolled"], clicker["online"]) == (True, True)
    assert (clicker["rssi"], clicker["battery_mv"], clicker["firmware"]) == (
        -61,
        3870,
        "1.0.0",
    )
    assert clicker["last_seen_at"] is not None
    spare = devices["spare"]
    assert (spare["enrolled"], spare["online"], spare["last_seen_at"]) == (
        False,
        False,
        None,
    )


def test_clicker_is_offline_after_forty_five_seconds(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    checkin(client)
    conn.execute(
        "UPDATE devices SET last_seen_at = datetime('now', '-46 seconds') "
        "WHERE device_id = ?",
        (CLICKER_ID,),
    )
    conn.commit()

    assert _devices(client, teacher)[CLICKER_ID]["online"] is False


def test_deleting_a_clicker_lets_it_enroll_again(staff_db, client):
    """A clicker whose flash was erased has a new secret: removing it resets it."""
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    checkin(client)
    assign(client, teacher, CLICKER_ID, get_user_id(conn, "student2"))

    locked_out = checkin(client, secret=OTHER_SECRET)
    removed = client.delete(f"/api/v1/staff/devices/{CLICKER_ID}", headers=teacher)
    re_enrolled = checkin(client, secret=OTHER_SECRET)

    assert locked_out.status_code == 401
    assert removed.status_code == 200
    assert re_enrolled.status_code == 200
    assert re_enrolled.json()["assigned"] is False
    assert _devices(client, teacher)[CLICKER_ID]["enrolled"] is True
