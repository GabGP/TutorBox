"""Mode 2 analytics: the teacher's tutor report at /api/v1/tutor/analytics."""

from tests.conftest import get_user_id

ANALYTICS = "/api/v1/tutor/analytics"
WEDNESDAY = "2026-11-11"  # its week runs Mon 2026-11-09 .. Sun 2026-11-15


def add_login(conn, username: str, session_id: str) -> str:
    conn.execute(
        "INSERT INTO sessions (id, user_id) VALUES (?, ?)",
        (session_id, get_user_id(conn, username)),
    )
    return session_id


def add_turn(conn, session_id, when, topic, problem=None, hint=0, correct=None):
    """One tutor turn; the child's text is a constant the report must never show."""
    conn.execute(
        "INSERT INTO turn_logs (session_id, user_input, final_response, hint_level, "
        "sympy_is_correct, sympy_evaluated_expression, concept_topic, timestamp) "
        "VALUES (?, 'texto privado', 'respuesta', ?, ?, ?, ?, ?)",
        (session_id, hint, correct, problem, topic, when),
    )


def seed_week(conn) -> None:
    ana = add_login(conn, "student1", "login-ana")
    beto = add_login(conn, "student2", "login-beto")
    teacher = add_login(conn, "teacher1", "login-teacher")
    # Ana: stuck on 3 + 4 until the last hint, then solves it; solves a fraction; chats.
    add_turn(conn, ana, "2026-11-10 09:00:00", "arithmetic", "3 + 4", 0, 0)
    add_turn(conn, ana, "2026-11-10 09:01:00", "arithmetic", "3 + 4", 1, 0)
    add_turn(conn, ana, "2026-11-10 09:02:00", "arithmetic", "3 + 4", 3, 0)
    add_turn(conn, ana, "2026-11-10 09:03:00", "arithmetic", "3 + 4", 3, 1)
    add_turn(conn, ana, "2026-11-10 09:05:00", "fractions", "1/2 + 1/4", 0, 1)
    add_turn(conn, ana, "2026-11-10 09:06:00", None)
    add_turn(conn, beto, "2026-11-11 10:00:00", "arithmetic", "5 × 6", 0, 1)
    # Not in the report: a teacher trying the tutor, and next week's turn.
    add_turn(conn, teacher, "2026-11-10 08:00:00", "pre_algebra", "x + 1 = 2", 3, 0)
    add_turn(conn, ana, "2026-11-16 09:00:00", "pre_algebra", "x + 2 = 5", 3, 0)
    conn.commit()


def test_the_weekly_report_shows_what_students_asked_and_got_stuck_on(
    staff_db, client, teacher_headers
):
    _, conn = staff_db
    seed_week(conn)

    response = client.get(
        ANALYTICS, params={"period": "week", "date": WEDNESDAY}, headers=teacher_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert "texto privado" not in response.text
    assert {k: body[k] for k in ("start", "end", "students", "sessions", "turns")} == {
        "start": "2026-11-09",
        "end": "2026-11-16",
        "students": 2,
        "sessions": 2,
        "turns": 7,
    }
    assert (body["most_asked_topic"], body["most_stuck_topic"]) == (
        "arithmetic",
        "arithmetic",
    )
    assert body["topics"] == [
        {"topic": "arithmetic", "turns": 5, "students": 2, "solved": 2, "stuck": 1},
        {"topic": "fractions", "turns": 1, "students": 1, "solved": 1, "stuck": 0},
    ]
    assert body["session_summaries"] == [
        {
            "student": "student2",
            "started_at": "2026-11-11 10:00:00",
            "last_turn_at": "2026-11-11 10:00:00",
            "turns": 1,
            "topics": ["arithmetic"],
            "solved": 1,
            "stuck": 0,
        },
        {
            "student": "student1",
            "started_at": "2026-11-10 09:00:00",
            "last_turn_at": "2026-11-10 09:06:00",
            "turns": 6,
            "topics": ["arithmetic", "fractions"],
            "solved": 2,
            "stuck": 1,
        },
    ]


def test_the_daily_report_keeps_only_that_day(staff_db, client, admin_headers):
    _, conn = staff_db
    seed_week(conn)

    response = client.get(
        ANALYTICS, params={"period": "day", "date": "2026-11-11"}, headers=admin_headers
    )

    body = response.json()
    assert (body["start"], body["end"], body["turns"]) == (
        "2026-11-11",
        "2026-11-12",
        1,
    )
    assert [s["student"] for s in body["session_summaries"]] == ["student2"]


def test_a_month_without_tutor_use_is_an_empty_report(
    staff_db, client, teacher_headers
):
    response = client.get(
        ANALYTICS, params={"period": "month"}, headers=teacher_headers
    )

    body = response.json()
    assert body["turns"] == 0 and body["topics"] == []
    assert body["most_asked_topic"] is None and body["most_stuck_topic"] is None


def test_students_cannot_read_the_tutor_report(staff_db, client, student_headers):
    assert client.get(ANALYTICS, headers=student_headers).status_code == 403
