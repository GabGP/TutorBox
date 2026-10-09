"""Migration 015: the clicker secret columns of devices and the device_id of sessions."""

import sqlite3

from core.db.migrations import apply_migrations


def _migrated_connection(tmp_path) -> sqlite3.Connection:
    db_path = str(tmp_path / "migrated.db")
    apply_migrations(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn: sqlite3.Connection, table_name: str) -> dict:
    return {
        row["name"]: row
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def test_migration_015_adds_nullable_secret_columns_to_devices(tmp_path):
    conn = _migrated_connection(tmp_path)

    columns = _table_columns(conn, "devices")
    conn.close()

    assert columns["secret_hash"]["type"] == "TEXT"
    assert columns["secret_hash"]["notnull"] == 0
    assert columns["secret_hash"]["dflt_value"] is None
    assert columns["secret_issued_at"]["type"] == "TIMESTAMP"
    assert columns["secret_issued_at"]["notnull"] == 0
    assert columns["secret_issued_at"]["dflt_value"] is None


def test_migration_015_adds_nullable_device_id_to_sessions(tmp_path):
    conn = _migrated_connection(tmp_path)

    columns = _table_columns(conn, "sessions")
    conn.close()

    assert columns["device_id"]["type"] == "TEXT"
    assert columns["device_id"]["notnull"] == 0
    assert columns["device_id"]["dflt_value"] is None


def test_migration_015_creates_the_sessions_device_index(tmp_path):
    conn = _migrated_connection(tmp_path)

    index_names = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
    }
    conn.close()

    assert "idx_sessions_device_id" in index_names


def test_migration_015_keeps_insert_without_new_columns_working(tmp_path):
    conn = _migrated_connection(tmp_path)
    user_id = conn.execute(
        "INSERT INTO users (username, hashed_pin) VALUES ('student1', 'hash')"
    ).lastrowid
    conn.execute("INSERT INTO devices (device_id) VALUES ('CLICKER_01')")
    conn.execute(
        "INSERT INTO sessions (id, user_id) VALUES ('session-digest-1', ?)",
        (user_id,),
    )
    conn.commit()

    device_row = conn.execute(
        "SELECT secret_hash, secret_issued_at FROM devices WHERE device_id = 'CLICKER_01'"
    ).fetchone()
    session_row = conn.execute(
        "SELECT device_id FROM sessions WHERE id = 'session-digest-1'"
    ).fetchone()
    conn.close()

    assert tuple(device_row) == (None, None)
    assert tuple(session_row) == (None,)


def test_migration_015_is_recorded_once_when_migrations_run_again(tmp_path):
    conn = _migrated_connection(tmp_path)
    conn.close()
    apply_migrations(str(tmp_path / "migrated.db"))

    conn = sqlite3.connect(str(tmp_path / "migrated.db"))
    versions = conn.execute(
        "SELECT COUNT(*) FROM schema_migrations WHERE version = 15"
    ).fetchone()[0]
    conn.close()

    assert versions == 1
