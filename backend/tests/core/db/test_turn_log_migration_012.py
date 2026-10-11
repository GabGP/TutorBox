import os
import sqlite3
import tempfile

import pytest

from core.db.migrations import apply_migrations

PEDAGOGY_COLUMNS = (
    "concept_topic",
    "concept_subconcept",
    "cnb_topic",
    "error_type",
    "scaffolding_strategy",
)


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


def turn_logs_columns_by_name(conn):
    rows = conn.execute("PRAGMA table_info(turn_logs)").fetchall()
    return {row["name"]: row for row in rows}


def test_migration_012_adds_five_pedagogy_columns(fresh_db):
    conn, _ = fresh_db
    columns = turn_logs_columns_by_name(conn)
    assert set(PEDAGOGY_COLUMNS).issubset(columns)


def test_migration_012_pedagogy_columns_are_nullable_text_without_default(fresh_db):
    conn, _ = fresh_db
    columns = turn_logs_columns_by_name(conn)
    for column_name in PEDAGOGY_COLUMNS:
        assert columns[column_name]["type"] == "TEXT"
        assert columns[column_name]["notnull"] == 0
        assert columns[column_name]["dflt_value"] is None


def test_migration_012_creates_concept_index(fresh_db):
    conn, _ = fresh_db
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cursor.fetchall()}
    assert "idx_turn_logs_concept" in indexes

    index_rows = conn.execute("PRAGMA index_info(idx_turn_logs_concept)").fetchall()
    assert [row["name"] for row in index_rows] == [
        "concept_topic",
        "concept_subconcept",
    ]


def test_migration_012_accepts_labels_outside_any_vocabulary(fresh_db):
    conn, _ = fresh_db
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin) VALUES (40, 'student4', 'hash')"
    )
    conn.execute("INSERT INTO sessions (id, user_id) VALUES ('s4', 40)")
    conn.execute(
        """
        INSERT INTO turn_logs (
            session_id, user_input, final_response, concept_topic, concept_subconcept,
            cnb_topic, error_type, scaffolding_strategy
        ) VALUES (
            's4', '2', 'ok', 'new_topic', 'new_subconcept',
            'new_cnb_topic', 'new_error_type', 'new_strategy'
        )
        """
    )
    conn.commit()

    row = conn.execute(
        "SELECT concept_topic, concept_subconcept, cnb_topic, error_type, "
        "scaffolding_strategy FROM turn_logs WHERE session_id = 's4'"
    ).fetchone()
    assert tuple(row) == (
        "new_topic",
        "new_subconcept",
        "new_cnb_topic",
        "new_error_type",
        "new_strategy",
    )
