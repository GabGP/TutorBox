"""Mode 3 API: a phone posts its queue of game events to /api/v1/games/events."""

import pytest

from tests.conftest import get_user_id

EVENTS = "/api/v1/games/events"
INSTALL_ID = "install-000000000001"
NEVER_ISSUED_AUTHORIZATION = "Bearer 123e4567-e89b-42d3-a456-426614174000"


def make_event(**overrides) -> dict:
    event = {
        "client_event_id": "evt-0000000000000001",
        "grade": "primero",
        "lesson_id": "sumar-jocotes",
        "round_index": 0,
        "attempt": 1,
        "is_correct": False,
        "answer": "4",
        "expected": "5",
        "occurred_at": "2026-10-09T15:04:05Z",
        "app_version": "1",
    }
    event.update(overrides)
    return event


def numbered_event(number: int, **overrides) -> dict:
    return make_event(client_event_id=f"evt-{number:016d}", **overrides)


def post_events(client, events, headers=None, install_id=INSTALL_ID):
    body = {"install_id": install_id, "events": events}
    return client.post(EVENTS, json=body, headers=headers)


def _count_rows(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM game_events").fetchone()[0]


def test_an_anonymous_phone_stores_its_new_events(temp_db, client):
    _, conn = temp_db

    response = post_events(
        client, [numbered_event(1), numbered_event(2), numbered_event(3)]
    )

    assert response.status_code == 200
    assert response.json() == {
        "accepted": 3,
        "duplicates": 0,
        "rejected": 0,
        "results": ["accepted", "accepted", "accepted"],
    }
    rows = conn.execute("SELECT install_id, student_id FROM game_events").fetchall()
    assert [tuple(row) for row in rows] == [(INSTALL_ID, None)] * 3


def test_resending_the_same_batch_stores_nothing_twice(temp_db, client):
    _, conn = temp_db
    batch = [numbered_event(1), numbered_event(2), numbered_event(3)]
    post_events(client, batch)

    response = post_events(client, batch)

    assert response.status_code == 200
    assert response.json() == {
        "accepted": 0,
        "duplicates": 3,
        "rejected": 0,
        "results": ["duplicate", "duplicate", "duplicate"],
    }
    assert _count_rows(conn) == 3


def test_a_batch_that_overlaps_a_stored_one_reports_each_event_in_order(
    temp_db, client
):
    _, conn = temp_db
    post_events(client, [numbered_event(1), numbered_event(2)])

    response = post_events(client, [numbered_event(2), numbered_event(3)])

    assert response.json()["results"] == ["duplicate", "accepted"]
    assert _count_rows(conn) == 3


def test_one_malformed_event_is_rejected_alone(temp_db, client):
    _, conn = temp_db
    malformed = numbered_event(9, grade="Primero")

    response = post_events(client, [numbered_event(1), malformed, numbered_event(2)])

    assert response.status_code == 200
    assert response.json()["results"] == ["accepted", "rejected", "accepted"]
    assert _count_rows(conn) == 2


def test_items_that_are_not_objects_are_rejected_alone(temp_db, client):
    _, conn = temp_db

    response = post_events(client, ["texto", 7, None, [], numbered_event(1)])

    assert response.status_code == 200
    assert response.json()["results"] == [
        "rejected",
        "rejected",
        "rejected",
        "rejected",
        "accepted",
    ]
    assert _count_rows(conn) == 1


def test_an_event_of_an_unknown_lesson_is_stored_without_labels(temp_db, client):
    _, conn = temp_db

    response = post_events(client, [numbered_event(1, lesson_id="leccion-nueva")])

    assert response.json()["results"] == ["accepted"]
    row = conn.execute(
        "SELECT cnb_topic, concept_topic, concept_subconcept FROM game_events"
    ).fetchone()
    assert tuple(row) == (None, None, None)


def test_extra_unknown_fields_are_ignored(temp_db, client):
    _, conn = temp_db
    body = {
        "install_id": INSTALL_ID,
        "events": [numbered_event(1, phone_model="Pixel 7")],
        "app_build": "42",
    }

    response = client.post(EVENTS, json=body)

    assert response.status_code == 200
    assert response.json()["results"] == ["accepted"]
    assert _count_rows(conn) == 1


def test_a_logged_in_students_events_carry_the_student_id(
    staff_db, client, student_headers
):
    _, conn = staff_db

    post_events(client, [numbered_event(1)], headers=student_headers)

    row = conn.execute("SELECT student_id FROM game_events").fetchone()
    assert row["student_id"] == get_user_id(conn, "student1")


def test_a_logged_in_teachers_events_are_stored_without_a_student(
    staff_db, client, teacher_headers
):
    _, conn = staff_db

    post_events(client, [numbered_event(1)], headers=teacher_headers)

    row = conn.execute("SELECT student_id FROM game_events").fetchone()
    assert row["student_id"] is None


def test_a_token_that_was_never_issued_still_stores_the_events_anonymously(
    temp_db, client
):
    _, conn = temp_db

    response = post_events(
        client,
        [numbered_event(1)],
        headers={"Authorization": NEVER_ISSUED_AUTHORIZATION},
    )

    assert response.status_code == 200
    row = conn.execute("SELECT student_id FROM game_events").fetchone()
    assert row["student_id"] is None


def test_a_malformed_authorization_value_still_stores_the_events_anonymously(
    temp_db, client
):
    _, conn = temp_db

    response = post_events(
        client, [numbered_event(1)], headers={"Authorization": "Bearer junk"}
    )

    assert response.status_code == 200
    row = conn.execute("SELECT student_id FROM game_events").fetchone()
    assert row["student_id"] is None


def test_a_token_after_logout_stores_the_events_anonymously(
    staff_db, client, student_headers
):
    _, conn = staff_db
    logout = client.post("/api/v1/auth/logout", headers=student_headers)
    assert logout.status_code == 200

    response = post_events(client, [numbered_event(1)], headers=student_headers)

    assert response.status_code == 200
    row = conn.execute("SELECT student_id FROM game_events").fetchone()
    assert row["student_id"] is None


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"events": [make_event()]}, id="no-install-id"),
        pytest.param(
            {"install_id": "short", "events": [make_event()]}, id="short-install-id"
        ),
        pytest.param({"install_id": INSTALL_ID}, id="no-events"),
        pytest.param({"install_id": INSTALL_ID, "events": []}, id="empty-events"),
        pytest.param(
            {"install_id": INSTALL_ID, "events": [make_event()] * 201},
            id="over-the-batch-limit",
        ),
        pytest.param(
            {"install_id": INSTALL_ID, "events": "texto"}, id="events-as-text"
        ),
    ],
)
def test_a_malformed_envelope_is_refused_and_stores_nothing(temp_db, client, body):
    _, conn = temp_db

    response = client.post(EVENTS, json=body)

    assert response.status_code == 422
    assert _count_rows(conn) == 0


def test_exactly_200_events_in_one_batch_are_all_accepted(temp_db, client):
    _, conn = temp_db
    batch = [numbered_event(number) for number in range(1, 201)]

    response = post_events(client, batch)

    assert response.status_code == 200
    assert response.json()["accepted"] == 200
    assert _count_rows(conn) == 200


def test_the_labels_reach_the_database_through_the_endpoint(temp_db, client):
    _, conn = temp_db

    post_events(
        client, [numbered_event(1, grade="tercero", lesson_id="division-residuo")]
    )

    row = conn.execute(
        "SELECT cnb_topic, concept_topic, concept_subconcept FROM game_events"
    ).fetchone()
    assert tuple(row) == ("division", "arithmetic", "multiplication_division")
