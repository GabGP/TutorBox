"""Migration 014: the misconception column of game_events."""

import sqlite3

from core.db.migrations import apply_migrations

INSERT_EVENT = (
    "INSERT INTO game_events (client_event_id, install_id, grade, lesson_id, "
    "round_index, attempt, is_correct, occurred_at, misconception) "
    "VALUES (?, 'install-000000000001', 'tercero', 'sumas-restas', 0, 1, 0, "
    "'2026-10-09 15:04:05', ?)"
)


def _migrated_connection(tmp_path) -> sqlite3.Connection:
    db_path = str(tmp_path / "migrated.db")
    apply_migrations(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def test_migration_014_adds_a_nullable_misconception_column(tmp_path):
    conn = _migrated_connection(tmp_path)

    columns = {
        row["name"]: row for row in conn.execute("PRAGMA table_info(game_events)")
    }
    conn.close()

    assert len(columns) == 18
    assert columns["misconception"]["type"] == "TEXT"
    assert columns["misconception"]["notnull"] == 0
    assert columns["misconception"]["dflt_value"] is None


def test_migration_014_stores_a_slug_outside_any_vocabulary_and_null(tmp_path):
    conn = _migrated_connection(tmp_path)

    conn.execute(INSERT_EVENT, ("evt-0000000000000001", "a_new_mistake"))
    conn.execute(INSERT_EVENT, ("evt-0000000000000002", None))
    stored = conn.execute("SELECT misconception FROM game_events ORDER BY id")
    misconceptions = [row["misconception"] for row in stored]
    conn.close()

    assert misconceptions == ["a_new_mistake", None]


def test_migration_014_is_recorded_once_when_migrations_run_again(tmp_path):
    conn = _migrated_connection(tmp_path)
    conn.close()
    apply_migrations(str(tmp_path / "migrated.db"))

    conn = sqlite3.connect(str(tmp_path / "migrated.db"))
    versions = conn.execute(
        "SELECT COUNT(*) FROM schema_migrations WHERE version = 14"
    ).fetchone()[0]
    conn.close()

    assert versions == 1
