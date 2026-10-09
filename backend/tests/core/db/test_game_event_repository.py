"""Game answer telemetry in game_events (core/db/game_event_repository.py)."""

import sqlite3
from dataclasses import replace

import pytest

from core.db.database import get_db_connection
from core.db.game_event_repository import GameEventRecord, insert_game_event
from tests.conftest import get_user_id


def make_record(**overrides: object) -> GameEventRecord:
    """Builds a valid game event, with the given fields overridden."""
    default_record = GameEventRecord(
        client_event_id="evt-0000000000000001",
        install_id="install-000000001",
        grade="primero",
        lesson_id="sumar-jocotes",
        round_index=0,
        attempt=1,
        is_correct=False,
        occurred_at="2026-10-09 15:04:05",
    )
    return replace(default_record, **overrides)


def test_insert_game_event_stores_every_column(seeded_db):
    _, conn = seeded_db
    user_id = get_user_id(conn, "student1")

    insert_game_event(
        conn,
        make_record(
            client_event_id="evt-0000000000000002",
            install_id="install-000000002",
            grade="segundo",
            lesson_id="sumar-restar",
            round_index=3,
            attempt=2,
            is_correct=True,
            occurred_at="2026-10-09 15:10:00",
            student_id=user_id,
            answer="8",
            expected="8",
            app_version="1.4.0",
            cnb_topic="suma_resta",
            concept_topic="arithmetic",
            concept_subconcept="addition_subtraction",
        ),
    )
    conn.commit()

    row = conn.execute(
        "SELECT client_event_id, install_id, grade, lesson_id, round_index, attempt, "
        "is_correct, occurred_at, student_id, answer, expected, app_version, "
        "cnb_topic, concept_topic, concept_subconcept FROM game_events"
    ).fetchone()
    assert tuple(row) == (
        "evt-0000000000000002",
        "install-000000002",
        "segundo",
        "sumar-restar",
        3,
        2,
        1,
        "2026-10-09 15:10:00",
        user_id,
        "8",
        "8",
        "1.4.0",
        "suma_resta",
        "arithmetic",
        "addition_subtraction",
    )


def test_insert_game_event_returns_true_for_new_id(seeded_db):
    _, conn = seeded_db
    assert insert_game_event(conn, make_record()) is True


def test_insert_game_event_returns_false_for_stored_id_and_keeps_one_row(seeded_db):
    _, conn = seeded_db
    insert_game_event(conn, make_record())

    was_inserted = insert_game_event(conn, make_record())
    conn.commit()

    assert was_inserted is False
    assert conn.execute("SELECT COUNT(*) FROM game_events").fetchone()[0] == 1


def test_insert_game_event_keeps_first_delivery_when_id_repeats(seeded_db):
    _, conn = seeded_db
    insert_game_event(conn, make_record(answer="4"))
    insert_game_event(conn, make_record(answer="9"))
    conn.commit()

    stored_answer = conn.execute("SELECT answer FROM game_events").fetchone()
    assert stored_answer["answer"] == "4"


def test_insert_game_event_stores_two_different_ids(seeded_db):
    _, conn = seeded_db
    insert_game_event(conn, make_record(client_event_id="evt-0000000000000001"))
    insert_game_event(conn, make_record(client_event_id="evt-0000000000000002"))
    conn.commit()

    assert conn.execute("SELECT COUNT(*) FROM game_events").fetchone()[0] == 2


def test_insert_game_event_leaves_optional_fields_null_when_omitted(seeded_db):
    _, conn = seeded_db
    insert_game_event(conn, make_record())
    conn.commit()

    row = conn.execute(
        "SELECT student_id, answer, expected, app_version, cnb_topic, "
        "concept_topic, concept_subconcept FROM game_events"
    ).fetchone()
    assert tuple(row) == (None, None, None, None, None, None, None)


def test_insert_game_event_stores_is_correct_as_one_or_zero(seeded_db):
    _, conn = seeded_db
    insert_game_event(conn, make_record(client_event_id="evt-correct", is_correct=True))
    insert_game_event(conn, make_record(client_event_id="evt-wrong", is_correct=False))
    conn.commit()

    rows = conn.execute(
        "SELECT client_event_id, is_correct FROM game_events ORDER BY id"
    ).fetchall()
    assert [tuple(row) for row in rows] == [("evt-correct", 1), ("evt-wrong", 0)]


def test_insert_game_event_still_raises_on_other_constraint_violations(seeded_db):
    _, conn = seeded_db
    with pytest.raises(sqlite3.IntegrityError):
        insert_game_event(conn, make_record(attempt=0))


def test_deleting_user_keeps_event_and_sets_student_id_null(seeded_db):
    _, conn = seeded_db
    user_id = get_user_id(conn, "student1")
    insert_game_event(conn, make_record(student_id=user_id))
    conn.commit()

    conn.execute("DELETE FROM users WHERE username = 'student1'")
    conn.commit()

    row = conn.execute("SELECT student_id FROM game_events").fetchone()
    assert row is not None
    assert row["student_id"] is None


def test_insert_game_event_does_not_commit(seeded_db):
    db_path, conn = seeded_db
    insert_game_event(conn, make_record())

    other_conn = get_db_connection(db_path)
    try:
        visible_row_count = other_conn.execute(
            "SELECT COUNT(*) FROM game_events"
        ).fetchone()[0]
    finally:
        other_conn.close()

    assert visible_row_count == 0
