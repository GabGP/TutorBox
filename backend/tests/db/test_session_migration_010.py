import os
import sqlite3
import tempfile

import pytest

from src.db.migrations import apply_migrations


@pytest.fixture
def fresh_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    apply_migrations(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    yield conn, db_path
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_migration_010_creates_expected_tables(fresh_db):
    conn, _ = fresh_db
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert {
        "quiz_sessions",
        "quiz_session_rounds",
        "quiz_session_votes",
    }.issubset(tables)


def test_migration_010_creates_expected_indexes(fresh_db):
    conn, _ = fresh_db
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cursor.fetchall()}
    assert {
        "idx_quiz_sessions_status",
        "idx_quiz_rounds_session",
        "idx_quiz_votes_round",
        "idx_quiz_votes_student",
        "idx_quiz_votes_analytics",
    }.issubset(indexes)


def test_migration_010_first_press_locks_unique_constraint(fresh_db):
    conn, _ = fresh_db
    # Seed user, session, and round
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin) VALUES (10, 'student1', 'hash')"
    )
    conn.execute(
        "INSERT INTO quiz_sessions (id, title, topic) VALUES ('s1', 'Session 1', 'math')"
    )
    conn.execute(
        "INSERT INTO quiz_session_rounds (id, session_id, round_index) VALUES ('r1', 's1', 0)"
    )
    conn.commit()

    # First vote should succeed
    conn.execute(
        """
        INSERT INTO quiz_session_votes (
            id, session_id, round_id, student_id, selected_option, is_correct
        ) VALUES ('v1', 's1', 'r1', 10, 'A', 1)
        """
    )
    conn.commit()

    # Second vote from the same student in the same round must fail with UNIQUE constraint violation
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
        conn.execute(
            """
            INSERT INTO quiz_session_votes (
                id, session_id, round_id, student_id, selected_option, is_correct
            ) VALUES ('v2', 's1', 'r1', 10, 'B', 0)
            """
        )


def test_migration_010_cascade_delete_session(fresh_db):
    conn, _ = fresh_db
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin) VALUES (20, 'student2', 'hash')"
    )
    conn.execute(
        "INSERT INTO quiz_sessions (id, title, topic) VALUES ('s2', 'Session 2', 'math')"
    )
    conn.execute(
        "INSERT INTO quiz_session_rounds (id, session_id, round_index) VALUES ('r2', 's2', 0)"
    )
    conn.execute(
        """
        INSERT INTO quiz_session_votes (
            id, session_id, round_id, student_id, selected_option, is_correct
        ) VALUES ('v20', 's2', 'r2', 20, 'C', 0)
        """
    )
    conn.commit()

    # Deleting session should cascade to rounds and votes
    conn.execute("DELETE FROM quiz_sessions WHERE id = 's2'")
    conn.commit()

    rounds = conn.execute(
        "SELECT * FROM quiz_session_rounds WHERE session_id = 's2'"
    ).fetchall()
    assert len(rounds) == 0
    votes = conn.execute(
        "SELECT * FROM quiz_session_votes WHERE session_id = 's2'"
    ).fetchall()
    assert len(votes) == 0


def test_migration_010_check_constraints(fresh_db):
    conn, _ = fresh_db
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin) VALUES (30, 'student3', 'hash')"
    )
    conn.execute(
        "INSERT INTO quiz_sessions (id, title, topic) VALUES ('s3', 'Session 3', 'math')"
    )
    conn.execute(
        "INSERT INTO quiz_session_rounds (id, session_id, round_index) VALUES ('r3', 's3', 0)"
    )
    conn.commit()

    # Invalid status in quiz_sessions
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        conn.execute(
            "INSERT INTO quiz_sessions (id, title, topic, status) VALUES ('s_bad', 'Bad', 'math', 'invalid_status')"
        )

    # Invalid selected_option in quiz_session_votes (must be A, B, C, D)
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        conn.execute(
            """
            INSERT INTO quiz_session_votes (
                id, session_id, round_id, student_id, selected_option, is_correct
            ) VALUES ('v_bad', 's3', 'r3', 30, 'E', 0)
            """
        )
