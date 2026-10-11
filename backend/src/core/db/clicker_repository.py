"""Persistence for hardware clickers: self-enrollment, credentials and last check-in.

A clicker row is the same `devices` row the teacher assigns to a student; Week 7 adds
the clicker's secret digest and the vitals it reports on check-in (migration 012).
"""

import sqlite3
from dataclasses import dataclass

__all__ = [
    "MAX_CLICKERS",
    "ONLINE_WINDOW_SECONDS",
    "SEEN_UPDATE_SECONDS",
    "ClickerRecord",
    "count_clickers",
    "enroll_or_claim_clicker",
    "get_clicker",
    "record_checkin",
]

# Self-enrollment stops at 100 rows, so a script on the Wi-Fi cannot flood the roster.
# ponytail: fixed cap, make it a setting if a school ever runs more than 100 clickers.
MAX_CLICKERS = 100
# Each clicker's last check-in is written at most this often (it polls every second).
SEEN_UPDATE_SECONDS = 15
# The fleet view calls a clicker online if it checked in within this window: three
# missed write intervals, so one slow refresh never flips it to offline.
ONLINE_WINDOW_SECONDS = 3 * SEEN_UPDATE_SECONDS


@dataclass(frozen=True)
class ClickerRecord:
    device_id: str
    assigned_user_id: int | None
    secret_hash: str | None


def get_clicker(conn: sqlite3.Connection, device_id: str) -> ClickerRecord | None:
    """Returns the clicker's row, or None when the device id is not registered."""
    row = conn.execute(
        "SELECT device_id, assigned_user_id, secret_hash FROM devices "
        "WHERE device_id = ?",
        (device_id,),
    ).fetchone()
    if row is None:
        return None
    return ClickerRecord(row[0], row[1], row[2])


def count_clickers(conn: sqlite3.Connection) -> int:
    """Number of registered devices, enrolled or not."""
    return int(conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0])


def enroll_or_claim_clicker(
    conn: sqlite3.Connection, device_id: str, secret_digest: str
) -> bool:
    """Stores the digest for a new device id, or for one a teacher pre-registered.

    Returns True when this call enrolled the clicker. A device id that already has a
    secret keeps it (the update's WHERE clause), so a second device cannot take over a
    clicker that is enrolled; the caller then rejects the mismatching secret.
    """
    cursor = conn.execute(
        "INSERT INTO devices (device_id, secret_hash) VALUES (?, ?) "
        "ON CONFLICT(device_id) DO UPDATE SET secret_hash = excluded.secret_hash "
        "WHERE devices.secret_hash IS NULL",
        (device_id, secret_digest),
    )
    return cursor.rowcount > 0


def record_checkin(
    conn: sqlite3.Connection,
    device_id: str,
    *,
    firmware: str | None,
    rssi: int | None,
    battery_mv: int | None,
) -> bool:
    """Saves the clicker's vitals unless they were saved less than 15 s ago.

    Returns True when the row was written. The staleness check is a plain read, so
    the 14 check-ins in 15 that change nothing never take SQLite's write lock away
    from the votes being cast at the same moment.
    """
    stale = conn.execute(
        "SELECT 1 FROM devices WHERE device_id = ? "
        "AND (last_seen_at IS NULL OR last_seen_at <= datetime('now', ?))",
        (device_id, f"-{SEEN_UPDATE_SECONDS} seconds"),
    ).fetchone()
    if stale is None:
        return False
    conn.execute(
        "UPDATE devices SET last_seen_at = CURRENT_TIMESTAMP, firmware = ?, "
        "last_rssi = ?, last_battery_mv = ? WHERE device_id = ?",
        (firmware, rssi, battery_mv, device_id),
    )
    return True
