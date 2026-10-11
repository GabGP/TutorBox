"""Class roster reads: each student with the clicker assigned to them, and the leftovers.

Read-only. A clicker counts as assigned only while its student is an active student
account. A clicker whose student was deleted, or whose account is no longer a
student's, is listed as unassigned instead.
"""

import sqlite3
from dataclasses import dataclass

__all__ = [
    "ClassStudent",
    "list_students_with_clickers",
    "list_unassigned_clicker_ids",
]


@dataclass(frozen=True)
class ClassStudent:
    user_id: int
    username: str
    # The clicker assigned to this student, or None.
    device_id: str | None


def list_students_with_clickers(conn: sqlite3.Connection) -> list[ClassStudent]:
    """Active students ordered by username, each with the lowest id of their clickers.

    The assignment allows one clicker per student, so the lowest id is the only one
    there is. The rule still holds if two rows ever exist: the student appears once.
    """
    rows = conn.execute(
        "SELECT u.id, u.username, "
        "(SELECT MIN(d.device_id) FROM devices d WHERE d.assigned_user_id = u.id) "
        "AS device_id "
        "FROM users u WHERE u.role = 'student' AND u.deleted_at IS NULL "
        "ORDER BY u.username"
    ).fetchall()
    return [
        ClassStudent(
            user_id=row["id"],
            username=row["username"],
            device_id=row["device_id"],
        )
        for row in rows
    ]


def list_unassigned_clicker_ids(conn: sqlite3.Connection) -> list[str]:
    """Clickers that no listed student shows, ordered by id.

    That covers a clicker with no student, one whose student's account is deleted,
    and one assigned to an account that is not a student's. The clicker chosen for
    each listed student is excluded, the same rule as list_students_with_clickers.
    """
    rows = conn.execute(
        "SELECT d.device_id FROM devices d "
        "WHERE d.device_id NOT IN ("
        "  SELECT MIN(shown.device_id) FROM devices shown "
        "  JOIN users u ON u.id = shown.assigned_user_id "
        "  WHERE u.role = 'student' AND u.deleted_at IS NULL "
        "  GROUP BY shown.assigned_user_id"
        ") ORDER BY d.device_id"
    ).fetchall()
    return [row["device_id"] for row in rows]
