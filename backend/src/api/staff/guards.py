"""Shared guards preventing appliance management lockout."""

import sqlite3

from fastapi import HTTPException, status

__all__ = ["ensure_managers_remain"]


def count_live_managers(conn: sqlite3.Connection) -> int:
    """Counts live users able to manage the appliance (teachers + admins)."""
    cursor = conn.execute(
        "SELECT COUNT(*) AS n FROM users "
        "WHERE role IN ('teacher', 'admin') AND deleted_at IS NULL"
    )
    row = cursor.fetchone()
    return int(row["n"]) if row else 0


def ensure_managers_remain(
    conn: sqlite3.Connection, target_role: str, *, verb: str
) -> None:
    """Rejects removing the last account able to manage the appliance.

    Without this, demoting or deleting the final teacher/admin would lock
    everyone out of staff management (students cannot reach /maestro/).
    """
    if target_role not in ("teacher", "admin"):
        return
    if count_live_managers(conn) <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot {verb} the last staff account. "
                "The appliance needs at least one teacher or admin."
            ),
        )
