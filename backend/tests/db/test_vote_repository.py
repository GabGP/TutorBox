import sqlite3

import pytest

from db.vote_repository import (
    count_votes_for_round,
    get_round_vote_distribution,
    get_session_vote_summary,
    get_votes_for_round,
    get_votes_for_student,
    has_student_voted,
    record_student_vote,
)
from session.exceptions import VoteAlreadyCastError
from session.models import TransportType


@pytest.fixture
def memory_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_pin TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE quiz_sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            status TEXT DEFAULT 'lobby',
            question_count INTEGER DEFAULT 0,
            current_round_index INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE quiz_session_rounds (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
            question_id TEXT NULL,
            round_index INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            duration_seconds INTEGER DEFAULT 30
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE quiz_session_votes (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
            round_id TEXT NOT NULL REFERENCES quiz_session_rounds(id) ON DELETE CASCADE,
            student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            transport_type TEXT NOT NULL DEFAULT 'web' CHECK(transport_type IN ('web', 'hardware', 'mock')),
            device_id TEXT NULL,
            selected_option TEXT NOT NULL CHECK(selected_option IN ('A', 'B', 'C', 'D')),
            is_correct INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
            misconception TEXT NULL,
            response_time_ms REAL NULL CHECK(response_time_ms IS NULL OR response_time_ms >= 0.0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(round_id, student_id)
        );
        """
    )
    # Seed users and session/rounds
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin) VALUES (1, 'alice', 'h1')"
    )
    conn.execute("INSERT INTO users (id, username, hashed_pin) VALUES (2, 'bob', 'h2')")
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin) VALUES (3, 'charlie', 'h3')"
    )
    conn.execute(
        "INSERT INTO quiz_sessions (id, title, topic) VALUES ('sess_v', 'Math', 'fractions')"
    )
    conn.execute(
        "INSERT INTO quiz_session_rounds (id, session_id, round_index) VALUES ('round_1', 'sess_v', 0)"
    )
    conn.execute(
        "INSERT INTO quiz_session_rounds (id, session_id, round_index) VALUES ('round_2', 'sess_v', 1)"
    )
    conn.commit()

    yield conn
    conn.close()


def test_record_student_vote_success(memory_db):
    assert has_student_voted(memory_db, "round_1", 1) is False

    vote = record_student_vote(
        memory_db,
        vote_id="v_101",
        session_id="sess_v",
        round_id="round_1",
        student_id=1,
        selected_option="B",
        is_correct=True,
        misconception=None,
        transport_type=TransportType.WEB.value,
        device_id="dev_web_1",
        response_time_ms=1250.5,
    )
    assert vote.id == "v_101"
    assert vote.student_id == 1
    assert vote.selected_option == "B"
    assert vote.is_correct is True
    assert vote.response_time_ms == 1250.5
    assert has_student_voted(memory_db, "round_1", 1) is True


def test_first_press_lock_raises_vote_already_cast_error(memory_db):
    record_student_vote(
        memory_db,
        vote_id="v_201",
        session_id="sess_v",
        round_id="round_1",
        student_id=2,
        selected_option="A",
        is_correct=False,
        misconception="inverted_fractions",
    )

    # Subsequent vote from same student in same round MUST raise VoteAlreadyCastError
    with pytest.raises(VoteAlreadyCastError) as exc_info:
        record_student_vote(
            memory_db,
            vote_id="v_202",
            session_id="sess_v",
            round_id="round_1",
            student_id=2,
            selected_option="C",
            is_correct=True,
        )
    assert exc_info.value.round_id == "round_1"
    assert exc_info.value.student_id == 2


def test_get_votes_for_round_and_counting(memory_db):
    assert count_votes_for_round(memory_db, "round_1") == 0
    assert len(get_votes_for_round(memory_db, "round_1")) == 0

    record_student_vote(
        memory_db,
        "v_a",
        "sess_v",
        "round_1",
        1,
        "A",
        is_correct=False,
        misconception="sign_flip",
    )
    record_student_vote(memory_db, "v_b", "sess_v", "round_1", 2, "B", is_correct=True)

    votes = get_votes_for_round(memory_db, "round_1")
    assert len(votes) == 2
    assert count_votes_for_round(memory_db, "round_1") == 2
    assert votes[0].selected_option == "A"
    assert votes[1].selected_option == "B"


def test_get_round_vote_distribution(memory_db):
    record_student_vote(memory_db, "v_1", "sess_v", "round_1", 1, "A", is_correct=False)
    record_student_vote(memory_db, "v_2", "sess_v", "round_1", 2, "A", is_correct=False)
    record_student_vote(memory_db, "v_3", "sess_v", "round_1", 3, "C", is_correct=True)

    dist = get_round_vote_distribution(memory_db, "round_1")
    assert dist == {"A": 2, "B": 0, "C": 1, "D": 0}


def test_get_votes_for_student_longitudinal(memory_db):
    record_student_vote(
        memory_db,
        "v_s1",
        "sess_v",
        "round_1",
        1,
        "A",
        is_correct=False,
        misconception="common_denom",
    )
    record_student_vote(memory_db, "v_s2", "sess_v", "round_2", 1, "C", is_correct=True)

    student_history = get_votes_for_student(memory_db, 1)
    assert len(student_history) == 2
    assert student_history[0].round_id == "round_1"
    assert student_history[0].misconception == "common_denom"
    assert student_history[1].round_id == "round_2"
    assert student_history[1].is_correct is True


def test_foreign_key_violation_raises(memory_db):
    with pytest.raises(sqlite3.IntegrityError):
        record_student_vote(
            memory_db, "v_bad", "sess_v", "round_1", 9999, "A", is_correct=False
        )


def test_vote_retrieval_failure_raises():
    from unittest.mock import MagicMock

    mock_conn = MagicMock(spec=sqlite3.Connection)
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.execute.return_value = mock_cursor

    with pytest.raises(RuntimeError, match="Failed to retrieve recorded vote"):
        record_student_vote(
            mock_conn, "v_fail", "sess_v", "round_1", 1, "A", is_correct=False
        )


def test_get_session_vote_summary(memory_db):
    total, correct = get_session_vote_summary(memory_db, "sess_v")
    assert total == 0
    assert correct == 0

    record_student_vote(
        memory_db, "v_sum1", "sess_v", "round_1", 1, "A", is_correct=True
    )
    record_student_vote(
        memory_db, "v_sum2", "sess_v", "round_1", 2, "B", is_correct=False
    )
    total, correct = get_session_vote_summary(memory_db, "sess_v")
    assert total == 2
    assert correct == 1
