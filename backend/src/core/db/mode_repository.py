"""Classroom-wide appliance mode (single row in appliance_state, see migration 011)."""

import sqlite3
from typing import Literal

ApplianceMode = Literal["quiz", "tutor", "apps"]


def get_mode(conn: sqlite3.Connection) -> ApplianceMode:
    """Returns the active mode, defaulting to quiz if the row is somehow missing."""
    row = conn.execute("SELECT mode FROM appliance_state WHERE id = 1").fetchone()
    return row[0] if row is not None else "quiz"


def set_mode(
    conn: sqlite3.Connection, mode: ApplianceMode, user_id: int | None
) -> None:
    """Upserts the active mode and who chose it. The caller commits."""
    conn.execute(
        "INSERT INTO appliance_state (id, mode, updated_by) VALUES (1, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET mode = excluded.mode, "
        "updated_by = excluded.updated_by, updated_at = CURRENT_TIMESTAMP",
        (mode, user_id),
    )
