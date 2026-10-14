"""Clicker enrollment and device-bound sessions (core/db/device_repository.py)."""

import sqlite3

from core.db.database import get_db_connection
from core.db.device_repository import (
    DeviceCredentials,
    count_devices,
    create_device_session,
    enroll_or_claim_device,
    get_device_credentials,
    revoke_device_sessions,
)
from tests.conftest import get_user_id, required

FIRST_SECRET_DIGEST = "digest-of-the-first-secret"
SECOND_SECRET_DIGEST = "digest-of-the-second-secret"
SESSION_DIGEST = "digest-of-the-clicker-bearer-token"


def insert_device(
    conn: sqlite3.Connection, device_id: str, assigned_user_id: int | None = None
) -> None:
    """Registers a clicker, optionally assigned to a student, and commits."""
    conn.execute(
        "INSERT INTO devices (device_id, assigned_user_id) VALUES (?, ?)",
        (device_id, assigned_user_id),
    )
    conn.commit()


def insert_session(
    conn: sqlite3.Connection,
    session_id: str,
    user_id: int,
    device_id: str | None,
    is_active: int = 1,
) -> None:
    """Inserts a login session and commits."""
    conn.execute(
        "INSERT INTO sessions (id, user_id, is_active, device_id) VALUES (?, ?, ?, ?)",
        (session_id, user_id, is_active, device_id),
    )
    conn.commit()


def read_session_is_active(conn: sqlite3.Connection, session_id: str) -> int:
    row = conn.execute(
        "SELECT is_active FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    return row["is_active"]


def test_get_device_credentials_returns_none_for_unknown_device(staff_db):
    _, conn = staff_db

    assert get_device_credentials(conn, "NO_SUCH_CLICKER") is None


def test_get_device_credentials_reports_unassigned_device_without_secret(staff_db):
    _, conn = staff_db
    insert_device(conn, "CLICKER_01")

    credentials = required(get_device_credentials(conn, "CLICKER_01"))

    assert credentials == DeviceCredentials(
        device_id="CLICKER_01",
        secret_hash=None,
        assigned_user_id=None,
        assigned_username=None,
    )


def test_get_device_credentials_returns_the_enrolled_secret_hash(staff_db):
    _, conn = staff_db
    insert_device(conn, "CLICKER_01")
    enroll_or_claim_device(conn, "CLICKER_01", FIRST_SECRET_DIGEST)
    conn.commit()

    credentials = required(get_device_credentials(conn, "CLICKER_01"))

    assert credentials.secret_hash == FIRST_SECRET_DIGEST


def test_get_device_credentials_returns_assigned_student_id_and_username(staff_db):
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    insert_device(conn, "CLICKER_01", student_id)

    credentials = required(get_device_credentials(conn, "CLICKER_01"))

    assert credentials.assigned_user_id == student_id
    assert credentials.assigned_username == "student1"


def test_get_device_credentials_reads_deleted_student_as_unassigned(staff_db):
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    insert_device(conn, "CLICKER_01", student_id)
    conn.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?", (student_id,)
    )
    conn.commit()

    credentials = required(get_device_credentials(conn, "CLICKER_01"))

    assert credentials == DeviceCredentials(
        device_id="CLICKER_01",
        secret_hash=None,
        assigned_user_id=None,
        assigned_username=None,
    )


def test_count_devices_is_zero_for_an_empty_fleet(staff_db):
    _, conn = staff_db

    assert count_devices(conn) == 0


def test_count_devices_counts_hand_added_and_enrolled_clickers(staff_db):
    _, conn = staff_db
    insert_device(conn, "CLICKER_01")
    insert_device(conn, "CLICKER_02")
    enroll_or_claim_device(conn, "CLICKER_03", FIRST_SECRET_DIGEST)
    conn.commit()

    assert count_devices(conn) == 3


def test_enroll_or_claim_device_inserts_a_new_device_with_digest_and_issue_time(
    staff_db,
):
    _, conn = staff_db

    was_stored = enroll_or_claim_device(conn, "CLICKER_01", FIRST_SECRET_DIGEST)
    conn.commit()

    row = conn.execute(
        "SELECT secret_hash, secret_issued_at, assigned_user_id "
        "FROM devices WHERE device_id = 'CLICKER_01'"
    ).fetchone()
    assert was_stored is True
    assert row["secret_hash"] == FIRST_SECRET_DIGEST
    assert row["secret_issued_at"] is not None
    assert row["assigned_user_id"] is None


def test_enroll_or_claim_device_claims_a_hand_added_device_and_keeps_its_student(
    staff_db,
):
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    insert_device(conn, "CLICKER_01", student_id)

    was_claimed = enroll_or_claim_device(conn, "CLICKER_01", FIRST_SECRET_DIGEST)
    conn.commit()

    credentials = required(get_device_credentials(conn, "CLICKER_01"))
    assert was_claimed is True
    assert credentials.secret_hash == FIRST_SECRET_DIGEST
    assert credentials.assigned_user_id == student_id


def test_enroll_or_claim_device_refuses_to_overwrite_an_existing_secret(staff_db):
    _, conn = staff_db
    enroll_or_claim_device(conn, "CLICKER_01", FIRST_SECRET_DIGEST)
    conn.commit()

    was_overwritten = enroll_or_claim_device(conn, "CLICKER_01", SECOND_SECRET_DIGEST)
    conn.commit()

    assert was_overwritten is False
    credentials = required(get_device_credentials(conn, "CLICKER_01"))
    assert credentials.secret_hash == FIRST_SECRET_DIGEST
    assert count_devices(conn) == 1


def test_enroll_or_claim_device_leaves_the_commit_to_the_caller(staff_db):
    db_path, conn = staff_db
    enroll_or_claim_device(conn, "CLICKER_01", FIRST_SECRET_DIGEST)

    other_conn = get_db_connection(db_path)
    try:
        seen_before_commit = get_device_credentials(other_conn, "CLICKER_01")
        conn.commit()
        seen_after_commit = required(get_device_credentials(other_conn, "CLICKER_01"))
    finally:
        other_conn.close()

    assert seen_before_commit is None
    assert seen_after_commit.secret_hash == FIRST_SECRET_DIGEST


def test_create_device_session_stores_session_bound_to_device(staff_db):
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    insert_device(conn, "CLICKER_01", student_id)

    create_device_session(conn, SESSION_DIGEST, student_id, "CLICKER_01")
    conn.commit()

    row = conn.execute(
        "SELECT id, user_id, is_active, device_id FROM sessions WHERE id = ?",
        (SESSION_DIGEST,),
    ).fetchone()
    assert tuple(row) == (SESSION_DIGEST, student_id, 1, "CLICKER_01")


def seed_sessions_for_revocation(conn: sqlite3.Connection) -> None:
    """Two active clicker sessions, one revoked clicker session, another clicker's
    session, and a phone login of the same student (device_id NULL)."""
    student1_id = get_user_id(conn, "student1")
    student2_id = get_user_id(conn, "student2")
    insert_device(conn, "CLICKER_01", student1_id)
    insert_device(conn, "CLICKER_02", student2_id)
    insert_session(conn, "clicker-1-first", student1_id, "CLICKER_01")
    insert_session(conn, "clicker-1-second", student1_id, "CLICKER_01")
    insert_session(conn, "clicker-1-revoked", student1_id, "CLICKER_01", is_active=0)
    insert_session(conn, "clicker-2-active", student2_id, "CLICKER_02")
    insert_session(conn, "phone-student1", student1_id, None)


def test_revoke_device_sessions_returns_count_of_active_sessions_revoked(staff_db):
    _, conn = staff_db
    seed_sessions_for_revocation(conn)

    revoked_count = revoke_device_sessions(conn, "CLICKER_01")
    conn.commit()

    assert revoked_count == 2
    assert read_session_is_active(conn, "clicker-1-first") == 0
    assert read_session_is_active(conn, "clicker-1-second") == 0


def test_revoke_device_sessions_leaves_another_devices_session_active(staff_db):
    _, conn = staff_db
    seed_sessions_for_revocation(conn)

    revoke_device_sessions(conn, "CLICKER_01")
    conn.commit()

    assert read_session_is_active(conn, "clicker-2-active") == 1


def test_revoke_device_sessions_leaves_phone_session_of_same_student_active(staff_db):
    _, conn = staff_db
    seed_sessions_for_revocation(conn)

    revoke_device_sessions(conn, "CLICKER_01")
    conn.commit()

    assert read_session_is_active(conn, "phone-student1") == 1


def test_revoke_device_sessions_returns_zero_when_called_again(staff_db):
    _, conn = staff_db
    seed_sessions_for_revocation(conn)
    revoke_device_sessions(conn, "CLICKER_01")
    conn.commit()

    second_revoked_count = revoke_device_sessions(conn, "CLICKER_01")

    assert second_revoked_count == 0
