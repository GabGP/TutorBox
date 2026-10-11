"""Week 7 clicker credentials and the login sessions issued to a clicker.

Receives digests already computed by the caller: never a secret or a bearer token.
"""

import sqlite3
from dataclasses import dataclass

__all__ = [
    "DeviceCredentials",
    "create_device_session",
    "get_device_credentials",
    "release_clicker_of_user",
    "revoke_device_sessions",
    "store_device_secret",
]


@dataclass(frozen=True)
class DeviceCredentials:
    """What device authentication needs to know about one clicker."""

    device_id: str
    # None until a secret has been issued.
    secret_hash: str | None
    # None when unassigned, or when the assigned account is deleted or is not a
    # student's.
    assigned_user_id: int | None
    assigned_username: str | None


def get_device_credentials(
    conn: sqlite3.Connection, device_id: str
) -> DeviceCredentials | None:
    """Returns the clicker's credentials, or None when no device has that id.

    Only an active student account counts as assigned: a clicker never gets a
    session for a teacher or an admin.
    """
    row = conn.execute(
        "SELECT d.device_id, d.secret_hash, u.id AS assigned_user_id, "
        "u.username AS assigned_username "
        "FROM devices d "
        "LEFT JOIN users u ON u.id = d.assigned_user_id AND u.deleted_at IS NULL "
        "AND u.role = 'student' "
        "WHERE d.device_id = ?",
        (device_id,),
    ).fetchone()
    if row is None:
        return None
    return DeviceCredentials(
        device_id=row["device_id"],
        secret_hash=row["secret_hash"],
        assigned_user_id=row["assigned_user_id"],
        assigned_username=row["assigned_username"],
    )


def store_device_secret(
    conn: sqlite3.Connection, device_id: str, secret_hash: str
) -> bool:
    """Stores the digest of a newly issued clicker secret, replacing any previous one.

    Returns True when a row was updated and False when the device does not exist.
    The caller commits.
    """
    cursor = conn.execute(
        "UPDATE devices SET secret_hash = ?, secret_issued_at = CURRENT_TIMESTAMP "
        "WHERE device_id = ?",
        (secret_hash, device_id),
    )
    return cursor.rowcount == 1


def create_device_session(
    conn: sqlite3.Connection, session_digest: str, user_id: int, device_id: str
) -> None:
    """Stores a session issued to a clicker, keyed by its bearer token's digest.

    The caller commits.
    """
    conn.execute(
        "INSERT INTO sessions (id, user_id, is_active, device_id) VALUES (?, ?, 1, ?)",
        (session_digest, user_id, device_id),
    )


def revoke_device_sessions(conn: sqlite3.Connection, device_id: str) -> int:
    """Deactivates the active sessions issued to a clicker and returns how many.

    Sessions of other devices and phone logins (device_id NULL) are left untouched.
    The caller commits.
    """
    cursor = conn.execute(
        "UPDATE sessions SET is_active = 0 WHERE device_id = ? AND is_active = 1",
        (device_id,),
    )
    return cursor.rowcount


def release_clicker_of_user(conn: sqlite3.Connection, user_id: int) -> str | None:
    """Unassigns the clicker the user holds and revokes the sessions issued to it.

    Returns the clicker's id, or None when the user holds none. A user holds one
    clicker at most: devices.assigned_user_id is unique. The user's phone logins are
    left untouched. The caller commits.
    """
    row = conn.execute(
        "SELECT device_id FROM devices WHERE assigned_user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None
    released_device_id: str = row["device_id"]
    revoke_device_sessions(conn, released_device_id)
    conn.execute(
        "UPDATE devices SET assigned_user_id = NULL WHERE device_id = ?",
        (released_device_id,),
    )
    return released_device_id
