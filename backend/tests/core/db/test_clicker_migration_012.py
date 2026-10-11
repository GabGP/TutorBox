"""Migration 012: clicker secret digest and last check-in columns on `devices`."""

import sqlite3

from core.db.clicker_repository import (
    enroll_or_claim_clicker,
    get_clicker,
    record_checkin,
)
from core.db.migrations import apply_migrations


def test_migration_012_adds_clicker_columns(tmp_path):
    db_path = str(tmp_path / "m012.db")
    apply_migrations(db_path)
    conn = sqlite3.connect(db_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(devices)")}
        versions = {
            row[0] for row in conn.execute("SELECT version FROM schema_migrations")
        }
    finally:
        conn.close()

    assert 12 in versions
    assert {
        "secret_hash",
        "last_seen_at",
        "last_rssi",
        "last_battery_mv",
        "firmware",
    }.issubset(columns)


def test_enroll_or_claim_never_replaces_an_existing_secret(temp_db):
    _, conn = temp_db

    assert enroll_or_claim_clicker(conn, "c1", "digest-1") is True
    assert enroll_or_claim_clicker(conn, "c1", "digest-2") is False
    conn.execute("INSERT INTO devices (device_id) VALUES ('c2')")
    assert enroll_or_claim_clicker(conn, "c2", "digest-3") is True

    assert get_clicker(conn, "c1").secret_hash == "digest-1"
    assert get_clicker(conn, "c2").secret_hash == "digest-3"
    assert get_clicker(conn, "missing") is None


def test_record_checkin_skips_unknown_devices(temp_db):
    _, conn = temp_db

    assert record_checkin(conn, "ghost", firmware=None, rssi=None, battery_mv=None) is (
        False
    )
