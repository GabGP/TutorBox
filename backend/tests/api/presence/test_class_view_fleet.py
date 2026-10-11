"""Fleet check: 15 clickers and 15 phones beat, and the class view shows them all online.

The arena is the one of the vote fleet test. Its 30 students all connect. The two
students of the staff roster (student1 and student2) never do, so they are listed as
absent and the class has 32 students in all.
"""

from tests.api.session.fleet_support import FLEET_SIZE, set_up_arena

HEARTBEAT_URL = "/api/v1/presence/heartbeat"
CLASS_URL = "/api/v1/presence/class"
ROSTER_STUDENT_COUNT = 2


def test_15_clickers_and_15_phones_beating_are_all_online_in_the_class_view(
    staff_db, client, presence_store
):
    _, conn = staff_db
    arena = set_up_arena(client, conn)
    for clicker in arena.clickers:
        beat = client.post(
            HEARTBEAT_URL,
            json={"rssi": -60, "battery_pct": 80},
            headers=clicker.headers,
        )
        assert beat.status_code == 204
    for phone in arena.phones:
        beat = client.post(HEARTBEAT_URL, headers=phone.headers)
        assert beat.status_code == 204

    response = client.get(CLASS_URL, headers=arena.teacher_headers)

    assert response.status_code == 200
    body = response.json()
    fleet_student_ids = {clicker.student_id for clicker in arena.clickers} | {
        phone.student_id for phone in arena.phones
    }
    online_student_ids = {
        row["user_id"] for row in body["students"] if row["status"] == "online"
    }
    assert online_student_ids == fleet_student_ids
    assert body["online"] == 2 * FLEET_SIZE
    assert body["total"] == 2 * FLEET_SIZE + ROSTER_STUDENT_COUNT
    clicker_statuses = [
        row["clicker"]["status"] for row in body["students"] if row["clicker"]
    ]
    assert clicker_statuses == ["online"] * FLEET_SIZE
