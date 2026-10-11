"""Class roster reads: students with their clicker, and the clickers left over."""

import sqlite3

from core.db.class_roster_repository import (
    ClassStudent,
    list_students_with_clickers,
    list_unassigned_clicker_ids,
)
from tests.conftest import get_user_id


def insert_device(
    conn: sqlite3.Connection, device_id: str, assigned_user_id: int | None = None
) -> None:
    conn.execute(
        "INSERT INTO devices (device_id, assigned_user_id) VALUES (?, ?)",
        (device_id, assigned_user_id),
    )
    conn.commit()


def soft_delete(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute(
        "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?", (user_id,)
    )
    conn.commit()


def test_students_are_listed_by_username_and_staff_are_left_out(staff_db):
    _, conn = staff_db
    conn.execute(
        "INSERT INTO users (username, hashed_pin, role) VALUES ('ana', 'x', 'student')"
    )
    conn.commit()

    students = list_students_with_clickers(conn)

    assert [student.username for student in students] == [
        "ana",
        "student1",
        "student2",
    ]


def test_a_deleted_student_is_not_listed(staff_db):
    _, conn = staff_db
    soft_delete(conn, get_user_id(conn, "student2"))

    students = list_students_with_clickers(conn)

    assert [student.username for student in students] == ["student1"]


def test_each_student_carries_the_clicker_assigned_to_them_or_none(staff_db):
    _, conn = staff_db
    insert_device(conn, "ESP32-A4CF12", get_user_id(conn, "student1"))

    students = list_students_with_clickers(conn)

    assert students == [
        ClassStudent(
            user_id=get_user_id(conn, "student1"),
            username="student1",
            device_id="ESP32-A4CF12",
        ),
        ClassStudent(
            user_id=get_user_id(conn, "student2"),
            username="student2",
            device_id=None,
        ),
    ]


def test_two_clickers_on_one_student_list_the_student_once_with_the_lowest_id():
    """The real table allows one clicker per student, so this table has no unique key."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL, "
        "role TEXT NOT NULL, deleted_at TIMESTAMP);"
        "CREATE TABLE devices (device_id TEXT PRIMARY KEY, assigned_user_id INTEGER);"
        "INSERT INTO users (id, username, role) VALUES (1, 'ana', 'student');"
        "INSERT INTO devices (device_id, assigned_user_id) VALUES "
        "('ESP32-B', 1), ('ESP32-A', 1);"
    )

    students = list_students_with_clickers(conn)
    unassigned = list_unassigned_clicker_ids(conn)
    conn.close()

    assert students == [ClassStudent(user_id=1, username="ana", device_id="ESP32-A")]
    assert unassigned == ["ESP32-B"]


def test_unassigned_clickers_are_those_no_listed_student_shows(staff_db):
    _, conn = staff_db
    insert_device(conn, "ESP32-B7C001")
    insert_device(conn, "ESP32-A4CF12", get_user_id(conn, "student1"))
    insert_device(conn, "ESP32-C00002", get_user_id(conn, "student2"))
    soft_delete(conn, get_user_id(conn, "student2"))
    insert_device(conn, "ESP32-D00003", get_user_id(conn, "teacher1"))

    unassigned = list_unassigned_clicker_ids(conn)

    assert unassigned == ["ESP32-B7C001", "ESP32-C00002", "ESP32-D00003"]


def test_without_clickers_nothing_is_unassigned(staff_db):
    _, conn = staff_db

    assert list_unassigned_clicker_ids(conn) == []
