"""Giving a clicker back and who counts as assigned (core/db/device_repository.py)."""

import sqlite3

import pytest

from core.db.database import get_db_connection
from core.db.device_repository import (
    DeviceCredentials,
    get_device_credentials,
    release_clicker_of_user,
)
from tests.conftest import get_user_id, required
from tests.core.db.test_device_repository import (
    insert_device,
    insert_session,
    read_session_is_active,
)


def read_assigned_user_id(conn: sqlite3.Connection, device_id: str) -> int | None:
    row = conn.execute(
        "SELECT assigned_user_id FROM devices WHERE device_id = ?", (device_id,)
    ).fetchone()
    return row["assigned_user_id"]


@pytest.mark.parametrize("staff_username", ["teacher1", "admin1"])
def test_get_device_credentials_reads_staff_account_as_unassigned(
    staff_db, staff_username
):
    _, conn = staff_db
    insert_device(conn, "CLICKER_01", get_user_id(conn, staff_username))

    credentials = required(get_device_credentials(conn, "CLICKER_01"))

    assert credentials == DeviceCredentials(
        device_id="CLICKER_01",
        secret_hash=None,
        assigned_user_id=None,
        assigned_username=None,
    )


def test_release_clicker_of_user_unassigns_the_clicker_and_returns_its_id(staff_db):
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    insert_device(conn, "CLICKER_01", student_id)

    released_device_id = release_clicker_of_user(conn, student_id)
    conn.commit()

    assert released_device_id == "CLICKER_01"
    assert read_assigned_user_id(conn, "CLICKER_01") is None


def test_release_clicker_of_user_revokes_the_clickers_sessions_only(staff_db):
    _, conn = staff_db
    student_id = get_user_id(conn, "student1")
    insert_device(conn, "CLICKER_01", student_id)
    insert_session(conn, "clicker-session", student_id, "CLICKER_01")
    insert_session(conn, "phone-session", student_id, None)

    release_clicker_of_user(conn, student_id)
    conn.commit()

    assert read_session_is_active(conn, "clicker-session") == 0
    assert read_session_is_active(conn, "phone-session") == 1


def test_release_clicker_of_user_leaves_another_users_clicker_alone(staff_db):
    _, conn = staff_db
    student1_id = get_user_id(conn, "student1")
    student2_id = get_user_id(conn, "student2")
    insert_device(conn, "CLICKER_01", student1_id)
    insert_device(conn, "CLICKER_02", student2_id)
    insert_session(conn, "other-clicker-session", student2_id, "CLICKER_02")

    release_clicker_of_user(conn, student1_id)
    conn.commit()

    assert read_assigned_user_id(conn, "CLICKER_02") == student2_id
    assert read_session_is_active(conn, "other-clicker-session") == 1


def test_release_clicker_of_user_returns_none_for_user_without_clicker(staff_db):
    _, conn = staff_db
    insert_device(conn, "CLICKER_01")

    released_device_id = release_clicker_of_user(conn, get_user_id(conn, "student1"))

    assert released_device_id is None


def test_release_clicker_of_user_leaves_the_commit_to_the_caller(staff_db):
    db_path, conn = staff_db
    student_id = get_user_id(conn, "student1")
    insert_device(conn, "CLICKER_01", student_id)
    release_clicker_of_user(conn, student_id)

    other_conn = get_db_connection(db_path)
    try:
        seen_before_commit = read_assigned_user_id(other_conn, "CLICKER_01")
        conn.commit()
        seen_after_commit = read_assigned_user_id(other_conn, "CLICKER_01")
    finally:
        other_conn.close()

    assert seen_before_commit == student_id
    assert seen_after_commit is None
