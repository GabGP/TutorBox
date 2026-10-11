"""Clicker check-in: trust-on-first-use enrollment, vitals and the round view."""

import hashlib
import time

from modes.quiz.session.events import get_shared_timers
from modes.quiz.session.timer import RoundTimer
from tests.api.clicker.helpers import (
    CLICKER_ID,
    OTHER_SECRET,
    SECRET,
    assign,
    checkin,
    clicker_headers,
    clicker_vote,
    seed_questions,
    start_match,
)
from tests.conftest import auth_headers, get_user_id


def _device_row(conn, device_id=CLICKER_ID):
    return conn.execute(
        "SELECT * FROM devices WHERE device_id = ?", (device_id,)
    ).fetchone()


def test_first_checkin_enrolls_an_unassigned_clicker(staff_db, client):
    _, conn = staff_db

    response = checkin(client)

    assert response.status_code == 200
    assert response.json() == {
        "device_id": CLICKER_ID,
        "assigned": False,
        "round_id": None,
        "round_open": False,
        "voted": False,
    }
    row = _device_row(conn)
    assert row["assigned_user_id"] is None
    # Only the digest is stored, never the secret itself.
    assert row["secret_hash"] == hashlib.sha256(SECRET.encode()).hexdigest()
    actions = [r[0] for r in conn.execute("SELECT action FROM audit_logs")]
    assert actions == ["device_enrolled"]


def test_same_secret_checks_in_again_but_another_secret_is_rejected(staff_db, client):
    _, conn = staff_db
    assert checkin(client).status_code == 200

    assert checkin(client).status_code == 200
    rejected = checkin(client, secret=OTHER_SECRET)

    assert rejected.status_code == 401
    assert rejected.json()["detail"] == (
        "Clicker not recognized: unknown id or wrong secret."
    )
    # The enrolled secret survives a takeover attempt.
    assert (
        _device_row(conn)["secret_hash"] == hashlib.sha256(SECRET.encode()).hexdigest()
    )
    enrollments = conn.execute(
        "SELECT COUNT(*) FROM audit_logs WHERE action = 'device_enrolled'"
    ).fetchone()[0]
    assert enrollments == 1


def test_teacher_registered_clicker_is_claimed_and_keeps_its_student(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    client.post("/api/v1/staff/devices", json={"device_id": "7"}, headers=teacher)
    assign(client, teacher, "7", get_user_id(conn, "student1"))

    response = checkin(client, device_id="7")

    assert response.status_code == 200
    assert response.json()["assigned"] is True
    assert _device_row(conn, "7")["secret_hash"] is not None


def test_missing_or_malformed_credentials_are_rejected(staff_db, client):
    url = "/api/v1/clicker/checkin"

    assert client.post(url, json={}).status_code == 422
    assert (
        client.post(
            url, json={}, headers=clicker_headers(device_id="bad id!")
        ).status_code
        == 422
    )
    assert (
        client.post(url, json={}, headers=clicker_headers(secret="ABCDEF")).status_code
        == 422
    )
    assert (
        client.post(
            url, json={}, headers=clicker_headers(secret=SECRET.upper())
        ).status_code
        == 422
    )


def test_enrollment_stops_at_one_hundred_clickers(staff_db, client):
    _, conn = staff_db
    conn.executemany(
        "INSERT INTO devices (device_id) VALUES (?)",
        [(f"pre-{index:03d}",) for index in range(100)],
    )
    conn.commit()

    refused = checkin(client, device_id="ESP32-NEW001")
    # A clicker the teacher already registered is claimed even at the cap.
    claimed = checkin(client, device_id="pre-042")

    assert refused.status_code == 403
    assert "limit" in refused.json()["detail"]
    assert _device_row(conn, "ESP32-NEW001") is None
    assert claimed.status_code == 200


def test_vitals_are_saved_at_most_every_fifteen_seconds(staff_db, client):
    _, conn = staff_db

    checkin(client, firmware="1.0.0", rssi=-55, battery_mv=3950)
    first = _device_row(conn)
    checkin(client, firmware="1.0.1", rssi=-70, battery_mv=3900)
    throttled = _device_row(conn)
    conn.execute(
        "UPDATE devices SET last_seen_at = datetime('now', '-20 seconds') "
        "WHERE device_id = ?",
        (CLICKER_ID,),
    )
    conn.commit()
    checkin(client, firmware="1.0.1", rssi=-70)
    refreshed = _device_row(conn)

    assert (first["firmware"], first["last_rssi"], first["last_battery_mv"]) == (
        "1.0.0",
        -55,
        3950,
    )
    assert first["last_seen_at"] is not None
    assert throttled["last_rssi"] == -55
    assert (refreshed["firmware"], refreshed["last_rssi"]) == ("1.0.1", -70)
    assert refreshed["last_battery_mv"] is None


def test_invalid_vitals_are_rejected(staff_db, client):
    assert checkin(client, rssi=10).status_code == 422
    assert checkin(client, battery_mv=-1).status_code == 422
    assert checkin(client, firmware="1.0 beta").status_code == 422


def test_round_view_follows_the_match(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    checkin(client)
    assign(client, teacher, CLICKER_ID, get_user_id(conn, "student1"))
    question_ids = seed_questions(conn)

    idle = checkin(client).json()
    session_id = start_match(client, teacher, question_ids)
    round_id = f"{session_id}_r0"
    opened = checkin(client).json()
    assert clicker_vote(client, round_id).status_code == 200
    voted = checkin(client).json()
    client.post(f"/api/v1/session/{session_id}/close", headers=teacher)
    closed = checkin(client).json()

    assert (idle["assigned"], idle["round_id"]) == (True, None)
    assert opened == {
        "device_id": CLICKER_ID,
        "assigned": True,
        "round_id": round_id,
        "round_open": True,
        "voted": False,
    }
    assert (voted["round_open"], voted["voted"]) == (True, True)
    assert (closed["round_open"], closed["voted"]) == (False, True)


def test_lobby_round_is_announced_but_not_open(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    created = client.post(
        "/api/v1/session",
        json={
            "title": "Lobby",
            "topic": "arithmetic",
            "question_ids": seed_questions(conn),
        },
        headers=teacher,
    )

    view = checkin(client).json()

    assert view["round_id"] == f"{created.json()['id']}_r0"
    assert view["round_open"] is False


def test_expired_countdown_is_not_open(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    session_id = start_match(client, teacher, seed_questions(conn))
    round_id = f"{session_id}_r0"
    expired = RoundTimer(5)
    expired.start(start_time=time.monotonic() - 60)
    get_shared_timers()[round_id] = expired

    view = checkin(client).json()

    assert view["round_id"] == round_id
    assert view["round_open"] is False


def test_session_without_rounds_reports_no_round(staff_db, client):
    _, conn = staff_db
    conn.execute(
        "INSERT INTO quiz_sessions (id, title, topic, status) "
        "VALUES ('s_empty', 'Empty', 'arithmetic', 'lobby')"
    )
    conn.commit()

    view = checkin(client).json()

    assert view["round_id"] is None
    assert view["round_open"] is False
