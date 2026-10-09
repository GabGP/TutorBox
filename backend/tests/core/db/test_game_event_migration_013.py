import os
import sqlite3
import tempfile

import pytest

from core.db.migrations import apply_migrations

GAME_EVENT_COLUMNS = {
    "id",
    "client_event_id",
    "install_id",
    "student_id",
    "grade",
    "lesson_id",
    "round_index",
    "attempt",
    "is_correct",
    "answer",
    "expected",
    "app_version",
    "occurred_at",
    "received_at",
    "cnb_topic",
    "concept_topic",
    "concept_subconcept",
}

NOT_NULL_COLUMNS = (
    "client_event_id",
    "install_id",
    "grade",
    "lesson_id",
    "round_index",
    "attempt",
    "is_correct",
    "occurred_at",
)

NULLABLE_COLUMNS = (
    "student_id",
    "answer",
    "expected",
    "app_version",
    "cnb_topic",
    "concept_topic",
    "concept_subconcept",
)

VALID_EVENT_VALUES = {
    "client_event_id": "evt-0000000000000001",
    "install_id": "install-000000001",
    "student_id": None,
    "grade": "primero",
    "lesson_id": "sumar-jocotes",
    "round_index": 0,
    "attempt": 1,
    "is_correct": 1,
    "answer": None,
    "expected": None,
    "app_version": None,
    "occurred_at": "2026-10-09 15:04:05",
    "cnb_topic": None,
    "concept_topic": None,
    "concept_subconcept": None,
}


@pytest.fixture
def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    apply_migrations(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    yield conn, db_path
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def game_events_columns_by_name(conn):
    rows = conn.execute("PRAGMA table_info(game_events)").fetchall()
    return {row["name"]: row for row in rows}


def insert_game_event_row(conn, **overrides):
    """Inserts one valid game_events row, with the given columns overridden."""
    values = {**VALID_EVENT_VALUES, **overrides}
    conn.execute(
        """
        INSERT INTO game_events (
            client_event_id, install_id, student_id, grade, lesson_id,
            round_index, attempt, is_correct, answer, expected, app_version,
            occurred_at, cnb_topic, concept_topic, concept_subconcept
        ) VALUES (
            :client_event_id, :install_id, :student_id, :grade, :lesson_id,
            :round_index, :attempt, :is_correct, :answer, :expected, :app_version,
            :occurred_at, :cnb_topic, :concept_topic, :concept_subconcept
        )
        """,
        values,
    )


def test_migration_013_creates_game_events_with_seventeen_columns(fresh_db):
    conn, _ = fresh_db
    columns = game_events_columns_by_name(conn)
    assert set(columns) == GAME_EVENT_COLUMNS


def test_migration_013_marks_required_columns_not_null_and_optional_nullable(fresh_db):
    conn, _ = fresh_db
    columns = game_events_columns_by_name(conn)
    for column_name in NOT_NULL_COLUMNS:
        assert columns[column_name]["notnull"] == 1
    for column_name in NULLABLE_COLUMNS:
        assert columns[column_name]["notnull"] == 0


def test_migration_013_client_event_id_is_unique(fresh_db):
    conn, _ = fresh_db
    insert_game_event_row(conn, client_event_id="evt-duplicate")
    with pytest.raises(sqlite3.IntegrityError):
        insert_game_event_row(conn, client_event_id="evt-duplicate")


@pytest.mark.parametrize(
    ("column_name", "invalid_value"),
    [("is_correct", 2), ("round_index", -1), ("attempt", 0)],
)
def test_migration_013_check_constraints_reject_out_of_range_values(
    fresh_db, column_name, invalid_value
):
    conn, _ = fresh_db
    with pytest.raises(sqlite3.IntegrityError):
        insert_game_event_row(conn, **{column_name: invalid_value})


def test_migration_013_accepts_labels_outside_any_vocabulary(fresh_db):
    conn, _ = fresh_db
    insert_game_event_row(
        conn,
        cnb_topic="new_cnb",
        concept_topic="new_topic",
        concept_subconcept="new_subconcept",
    )
    conn.commit()

    row = conn.execute(
        "SELECT cnb_topic, concept_topic, concept_subconcept FROM game_events"
    ).fetchone()
    assert tuple(row) == ("new_cnb", "new_topic", "new_subconcept")


def test_migration_013_creates_concept_index(fresh_db):
    conn, _ = fresh_db
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cursor.fetchall()}
    assert "idx_game_events_concept" in indexes

    index_rows = conn.execute("PRAGMA index_info(idx_game_events_concept)").fetchall()
    assert [row["name"] for row in index_rows] == [
        "concept_topic",
        "concept_subconcept",
    ]


def test_migration_013_database_fills_received_at_when_omitted(fresh_db):
    conn, _ = fresh_db
    insert_game_event_row(conn)
    conn.commit()

    received_at = conn.execute("SELECT received_at FROM game_events").fetchone()
    assert received_at["received_at"] is not None
