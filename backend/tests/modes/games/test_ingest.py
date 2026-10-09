"""Ingestion of game events into game_events against a real database (modes/games/ingest.py)."""

import pytest

from core.db.database import get_db_connection
from modes.games.ingest import ACCEPTED, DUPLICATE, REJECTED, ingest_events
from tests.conftest import get_user_id

INSTALL_ID = "install-000000000001"


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


def _count_rows(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM game_events").fetchone()[0]


def _row_for(conn, client_event_id: str):
    return conn.execute(
        "SELECT * FROM game_events WHERE client_event_id = ?", (client_event_id,)
    ).fetchone()


def test_a_valid_event_is_accepted_and_stored_with_its_fields(seeded_db):
    _, conn = seeded_db

    statuses = ingest_events(conn, INSTALL_ID, None, [make_event()])

    assert statuses == [ACCEPTED]
    row = _row_for(conn, "evt-0000000000000001")
    assert row["install_id"] == INSTALL_ID
    assert row["student_id"] is None
    assert (row["grade"], row["lesson_id"]) == ("primero", "sumar-jocotes")
    assert (row["round_index"], row["attempt"]) == (0, 1)
    assert (row["answer"], row["expected"], row["app_version"]) == ("4", "5", "1")


@pytest.mark.parametrize(("is_correct", "stored"), [(True, 1), (False, 0)])
def test_is_correct_is_stored_as_one_or_zero(seeded_db, is_correct, stored):
    _, conn = seeded_db

    ingest_events(conn, INSTALL_ID, None, [make_event(is_correct=is_correct)])

    assert _row_for(conn, "evt-0000000000000001")["is_correct"] == stored


def test_occurred_at_is_stored_in_utc_sqlite_format(seeded_db):
    _, conn = seeded_db

    ingest_events(
        conn,
        INSTALL_ID,
        None,
        [make_event(occurred_at="2026-10-09T09:04:05-06:00")],
    )

    assert _row_for(conn, "evt-0000000000000001")["occurred_at"] == (
        "2026-10-09 15:04:05"
    )


def test_occurred_at_keeps_four_year_digits_and_drops_fractions_of_a_second(seeded_db):
    _, conn = seeded_db

    ingest_events(
        conn,
        INSTALL_ID,
        None,
        [make_event(occurred_at="0900-01-02T03:04:05.678Z")],
    )

    assert _row_for(conn, "evt-0000000000000001")["occurred_at"] == (
        "0900-01-02 03:04:05"
    )


@pytest.mark.parametrize(
    ("grade", "lesson_id", "labels"),
    [
        (
            "primero",
            "sumar-jocotes",
            ("suma_resta", "arithmetic", "addition_subtraction"),
        ),
        ("primero", "arriba-abajo", ("ubicacion", None, None)),
    ],
)
def test_the_lesson_labels_are_stored(seeded_db, grade, lesson_id, labels):
    _, conn = seeded_db

    ingest_events(
        conn, INSTALL_ID, None, [make_event(grade=grade, lesson_id=lesson_id)]
    )

    row = _row_for(conn, "evt-0000000000000001")
    assert (row["cnb_topic"], row["concept_topic"], row["concept_subconcept"]) == labels


@pytest.mark.parametrize(
    ("grade", "lesson_id"),
    [("primero", "leccion-que-no-existe"), ("cuarto", "fracciones")],
)
def test_an_unknown_lesson_or_grade_is_stored_without_labels(
    seeded_db, grade, lesson_id
):
    _, conn = seeded_db

    statuses = ingest_events(
        conn, INSTALL_ID, None, [make_event(grade=grade, lesson_id=lesson_id)]
    )

    assert statuses == [ACCEPTED]
    row = _row_for(conn, "evt-0000000000000001")
    assert (row["cnb_topic"], row["concept_topic"], row["concept_subconcept"]) == (
        None,
        None,
        None,
    )


def test_the_given_student_id_is_stored(seeded_db):
    _, conn = seeded_db
    student_id = get_user_id(conn, "student1")

    ingest_events(conn, INSTALL_ID, student_id, [make_event()])

    assert _row_for(conn, "evt-0000000000000001")["student_id"] == student_id


def test_the_same_id_twice_in_one_call_stores_one_row(seeded_db):
    _, conn = seeded_db

    statuses = ingest_events(conn, INSTALL_ID, None, [make_event(), make_event()])

    assert statuses == [ACCEPTED, DUPLICATE]
    assert _count_rows(conn) == 1


def test_calling_twice_with_the_same_events_stores_them_once(seeded_db):
    _, conn = seeded_db
    events = [
        make_event(client_event_id="evt-0000000000000001"),
        make_event(client_event_id="evt-0000000000000002"),
    ]

    first = ingest_events(conn, INSTALL_ID, None, events)
    second = ingest_events(conn, INSTALL_ID, None, events)

    assert first == [ACCEPTED, ACCEPTED]
    assert second == [DUPLICATE, DUPLICATE]
    assert _count_rows(conn) == 2


def test_statuses_come_back_in_order_for_a_mixed_list(seeded_db):
    _, conn = seeded_db
    ingest_events(
        conn, INSTALL_ID, None, [make_event(client_event_id="evt-0000000000000002")]
    )
    mixed = [
        make_event(client_event_id="evt-0000000000000001"),
        make_event(client_event_id="evt-0000000000000003", grade="Primero"),
        make_event(client_event_id="evt-0000000000000002"),
        "texto",
    ]

    statuses = ingest_events(conn, INSTALL_ID, None, mixed)

    assert statuses == [ACCEPTED, REJECTED, DUPLICATE, REJECTED]


def test_a_rejected_event_stores_nothing(seeded_db):
    _, conn = seeded_db

    statuses = ingest_events(conn, INSTALL_ID, None, [make_event(round_index=-1)])

    assert statuses == [REJECTED]
    assert _count_rows(conn) == 0


def test_an_empty_list_returns_no_statuses(seeded_db):
    _, conn = seeded_db

    assert ingest_events(conn, INSTALL_ID, None, []) == []


def test_ingest_does_not_commit_so_the_caller_decides(seeded_db):
    db_path, conn = seeded_db

    ingest_events(conn, INSTALL_ID, None, [make_event()])

    other_connection = get_db_connection(db_path)
    try:
        assert _count_rows(other_connection) == 0
    finally:
        other_connection.close()
