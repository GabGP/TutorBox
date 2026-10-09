"""Mode 3 API: staff read the counts of stored game events at /api/v1/games/events/summary."""

import pytest

from tests.api.games.test_games_api import INSTALL_ID, numbered_event, post_events

SUMMARY = "/api/v1/games/events/summary"
OTHER_INSTALL_ID = "install-000000000002"


def test_a_teacher_reads_the_counts_of_what_the_phones_sent(
    staff_db, client, teacher_headers
):
    post_events(
        client,
        [
            numbered_event(1),
            numbered_event(2, is_correct=True, answer="5"),
            numbered_event(3, lesson_id="arriba-abajo"),
        ],
    )
    post_events(client, [numbered_event(4)], install_id=OTHER_INSTALL_ID)

    response = client.get(SUMMARY, headers=teacher_headers)

    assert response.status_code == 200
    assert response.json() == {
        "events": 4,
        "wrong_events": 3,
        "installs": 2,
        "lessons": [
            {
                "grade": "primero",
                "lesson_id": "sumar-jocotes",
                "cnb_topic": "suma_resta",
                "concept_topic": "arithmetic",
                "concept_subconcept": "addition_subtraction",
                "events": 3,
                "wrong_events": 2,
            },
            {
                "grade": "primero",
                "lesson_id": "arriba-abajo",
                "cnb_topic": "ubicacion",
                "concept_topic": None,
                "concept_subconcept": None,
                "events": 1,
                "wrong_events": 1,
            },
        ],
    }


def test_an_admin_reads_an_empty_summary(staff_db, client, admin_headers):
    response = client.get(SUMMARY, headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == {
        "events": 0,
        "wrong_events": 0,
        "installs": 0,
        "lessons": [],
    }


def test_an_install_id_counts_one_phone_for_the_sync_test(
    staff_db, client, teacher_headers
):
    phone_events = [numbered_event(number) for number in range(1, 8)]
    post_events(client, phone_events)
    post_events(client, phone_events)  # the phone resends: nothing is counted twice
    post_events(client, [numbered_event(99)], install_id=OTHER_INSTALL_ID)

    response = client.get(
        SUMMARY, params={"install_id": INSTALL_ID}, headers=teacher_headers
    )

    assert response.json()["events"] == 7
    assert response.json()["installs"] == 1


def test_a_student_may_not_read_the_summary(staff_db, client, student_headers):
    response = client.get(SUMMARY, headers=student_headers)

    assert response.status_code == 403


def test_the_summary_needs_a_login(temp_db, client):
    response = client.get(SUMMARY)

    assert response.status_code == 401


@pytest.mark.parametrize("install_id", ["short", "has spaces in the id!", "a" * 65])
def test_a_malformed_install_id_is_refused(
    staff_db, client, teacher_headers, install_id
):
    response = client.get(
        SUMMARY, params={"install_id": install_id}, headers=teacher_headers
    )

    assert response.status_code == 422
