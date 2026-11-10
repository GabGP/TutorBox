"""Mode 1 analytics: the teacher's weekly/monthly report at /api/v1/quiz/analytics."""

import itertools
from datetime import date

import pytest

from src.core.db.periods import period_bounds
from tests.conftest import get_user_id

ANALYTICS = "/api/v1/quiz/analytics"
WEDNESDAY = "2026-11-11"  # its week runs Mon 2026-11-09 .. Sun 2026-11-15
_ids = itertools.count()


def add_question(conn, topic: str) -> str:
    question_id = f"q-{next(_ids)}"
    conn.execute(
        "INSERT INTO quiz_questions (id, topic, subconcept, question_text, "
        "options_json, correct_option, distractors_json) "
        "VALUES (?, ?, 'any', '¿2 + 2?', '{}', 'A', '[]')",
        (question_id, topic),
    )
    return question_id


def add_vote(conn, student, question_id, correct, when, misconception=None):
    """One answer of one student to one question, in its own session round."""
    n = next(_ids)
    conn.execute(
        "INSERT INTO quiz_sessions (id, title, topic) VALUES (?, 'Repaso', 'fractions')",
        (f"s-{n}",),
    )
    conn.execute(
        "INSERT INTO quiz_session_rounds (id, session_id, question_id, round_index) "
        "VALUES (?, ?, ?, 0)",
        (f"r-{n}", f"s-{n}", question_id),
    )
    conn.execute(
        "INSERT INTO quiz_session_votes (id, session_id, round_id, student_id, "
        "selected_option, is_correct, misconception, created_at) "
        "VALUES (?, ?, ?, ?, 'B', ?, ?, ?)",
        (f"v-{n}", f"s-{n}", f"r-{n}", student, int(correct), misconception, when),
    )


def test_the_weekly_report_ranks_topics_and_compares_with_last_week(
    staff_db, client, teacher_headers
):
    _, conn = staff_db
    ana, beto = get_user_id(conn, "student1"), get_user_id(conn, "student2")
    sums, fracs = add_question(conn, "arithmetic"), add_question(conn, "fractions")
    # last week: arithmetic 0/2, fractions 2/2
    add_vote(conn, ana, sums, False, "2026-11-03 15:00:00", "carry_omitted")
    add_vote(conn, beto, sums, False, "2026-11-04 15:00:00", "carry_omitted")
    add_vote(conn, ana, fracs, True, "2026-11-05 15:00:00")
    add_vote(conn, beto, fracs, True, "2026-11-06 15:00:00")
    # a topic only practiced last week is not in this week's report
    add_vote(
        conn,
        ana,
        add_question(conn, "decimals_percentages"),
        True,
        "2026-11-07 09:00:00",
    )
    # this week: arithmetic 2/2, fractions 1/2
    add_vote(conn, ana, sums, True, "2026-11-09 00:00:00")
    add_vote(conn, beto, sums, True, "2026-11-10 15:00:00")
    add_vote(conn, ana, fracs, True, "2026-11-11 15:00:00")
    add_vote(conn, beto, fracs, False, "2026-11-15 23:59:59", "add_denominators")
    # next week: outside the report
    add_vote(conn, ana, fracs, False, "2026-11-16 00:00:00", "add_denominators")
    conn.commit()

    response = client.get(
        ANALYTICS, params={"period": "week", "date": WEDNESDAY}, headers=teacher_headers
    )

    assert response.status_code == 200
    assert response.json() == {
        "period": "week",
        "start": "2026-11-09",
        "end": "2026-11-16",
        "students": 2,
        "answers": 4,
        "correct": 3,
        "accuracy": 75.0,
        "best_topic": "arithmetic",
        "weakest_topic": "fractions",
        "most_improved_topic": "arithmetic",
        "topics": [
            {
                "topic": "arithmetic",
                "answers": 2,
                "correct": 2,
                "accuracy": 100.0,
                "previous_accuracy": 0.0,
                "change": 100.0,
            },
            {
                "topic": "fractions",
                "answers": 2,
                "correct": 1,
                "accuracy": 50.0,
                "previous_accuracy": 100.0,
                "change": -50.0,
            },
        ],
        "misconceptions": [
            {
                "misconception": "add_denominators",
                "topic": "fractions",
                "wrong_answers": 1,
            }
        ],
    }


def test_a_month_without_answers_is_an_empty_report(staff_db, client, admin_headers):
    response = client.get(
        ANALYTICS, params={"period": "month", "date": WEDNESDAY}, headers=admin_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert (body["start"], body["end"]) == ("2026-11-01", "2026-12-01")
    assert body["answers"] == 0 and body["accuracy"] == 0.0
    assert body["topics"] == [] and body["best_topic"] is None


def test_a_vote_whose_question_is_gone_counts_under_the_session_topic(
    staff_db, client, teacher_headers
):
    _, conn = staff_db
    add_vote(conn, get_user_id(conn, "student1"), None, True, "2026-11-10 09:00:00")
    conn.commit()

    response = client.get(
        ANALYTICS, params={"date": WEDNESDAY}, headers=teacher_headers
    )

    topic = response.json()["topics"][0]
    assert (topic["topic"], topic["previous_accuracy"], topic["change"]) == (
        "fractions",
        None,
        None,
    )


def test_students_cannot_read_the_class_report(staff_db, client, student_headers):
    assert client.get(ANALYTICS, headers=student_headers).status_code == 403


def test_an_unknown_period_is_rejected(staff_db, client, teacher_headers):
    response = client.get(ANALYTICS, params={"period": "year"}, headers=teacher_headers)
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("period", "day", "bounds"),
    [
        ("day", date(2026, 3, 1), ("2026-02-28", "2026-03-01", "2026-03-02")),
        ("week", date(2026, 11, 9), ("2026-11-02", "2026-11-09", "2026-11-16")),
        ("week", date(2026, 11, 15), ("2026-11-02", "2026-11-09", "2026-11-16")),
        ("month", date(2026, 12, 31), ("2026-11-01", "2026-12-01", "2027-01-01")),
        ("month", date(2027, 1, 15), ("2026-12-01", "2027-01-01", "2027-02-01")),
        ("month", date(2028, 3, 1), ("2028-02-01", "2028-03-01", "2028-04-01")),
    ],
)
def test_period_bounds_cover_weeks_and_month_rollovers(period, day, bounds):
    assert tuple(d.isoformat() for d in period_bounds(period, day)) == bounds
