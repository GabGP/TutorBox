"""Audit trail helper."""

import sqlite3

VALID_ACTIONS = frozenset(
    {
        "signup",
        "user_created",
        "pin_reset",
        "username_changed",
        "pin_changed",
        "account_deleted",
        "account_recovered",
        "device_registered",
        "device_assigned",
        "device_unassigned",
        "device_deleted",
        "quiz_question_generated",
        "quiz_question_created",
        "quiz_question_deleted",
    }
)


def record_audit(
    conn: sqlite3.Connection,
    *,
    actor_user_id: int | None,
    action: str,
    target_user_id: int | None = None,
) -> None:
    """
    Records an append-only audit trail event in the audit_logs table.
    """
    if action not in VALID_ACTIONS:
        raise ValueError(f"Unknown audit action: {action}")

    conn.execute(
        "INSERT INTO audit_logs (actor_user_id, action, target_user_id) VALUES (?, ?, ?)",
        (actor_user_id, action, target_user_id),
    )
