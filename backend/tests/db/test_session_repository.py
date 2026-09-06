import sqlite3

import pytest

from db.session_repository import (
    create_quiz_round,
    create_quiz_session,
    get_quiz_round,
    get_quiz_session,
    get_round_by_index,
    list_rounds_for_session,
    update_quiz_round_status,
    update_quiz_session_status,
)
from session.models import RoundStatus, SessionStatus


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
        CREATE TABLE quiz_questions (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            subconcept TEXT NOT NULL,
            question_text TEXT NOT NULL,
            options_json TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            distractors_json TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE quiz_sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            teacher_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'lobby',
            question_count INTEGER NOT NULL DEFAULT 0,
            current_round_index INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP NULL,
            ended_at TIMESTAMP NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE quiz_session_rounds (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
            question_id TEXT NULL REFERENCES quiz_questions(id) ON DELETE SET NULL,
            round_index INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            opened_at TIMESTAMP NULL,
            closed_at TIMESTAMP NULL,
            duration_seconds INTEGER NOT NULL DEFAULT 30
        );
        """
    )
    yield conn
    conn.close()


def test_create_and_get_quiz_session(memory_db):
    session = create_quiz_session(
        memory_db,
        session_id="sess_101",
        title="Fractions Challenge",
        topic="fractions",
        teacher_id=None,
        question_count=5,
    )
    assert session.id == "sess_101"
    assert session.title == "Fractions Challenge"
    assert session.topic == "fractions"
    assert session.status == SessionStatus.LOBBY.value
    assert session.question_count == 5
    assert session.current_round_index == 0

    retrieved = get_quiz_session(memory_db, "sess_101")
    assert retrieved is not None
    assert retrieved.id == "sess_101"
    assert retrieved.title == "Fractions Challenge"

    missing = get_quiz_session(memory_db, "non_existent")
    assert missing is None


def test_update_quiz_session_status(memory_db):
    create_quiz_session(memory_db, "sess_202", "Algebra", "algebra", question_count=3)

    success = update_quiz_session_status(
        memory_db,
        "sess_202",
        status=SessionStatus.ACTIVE.value,
        started_at="2026-09-05T08:00:00Z",
        current_round_index=1,
    )
    assert success is True

    updated = get_quiz_session(memory_db, "sess_202")
    assert updated is not None
    assert updated.status == SessionStatus.ACTIVE.value
    assert updated.started_at == "2026-09-05T08:00:00Z"
    assert updated.current_round_index == 1

    # End session
    update_quiz_session_status(
        memory_db,
        "sess_202",
        status=SessionStatus.COMPLETED.value,
        ended_at="2026-09-05T08:15:00Z",
    )
    completed = get_quiz_session(memory_db, "sess_202")
    assert completed is not None
    assert completed.status == SessionStatus.COMPLETED.value
    assert completed.ended_at == "2026-09-05T08:15:00Z"

    # Non-existent session returns False
    assert update_quiz_session_status(memory_db, "sess_none", "active") is False


def test_create_and_manage_quiz_rounds(memory_db):
    create_quiz_session(memory_db, "sess_303", "Decimals", "decimals", question_count=2)

    round_0 = create_quiz_round(
        memory_db,
        round_id="rnd_0",
        session_id="sess_303",
        round_index=0,
        question_id=None,
        duration_seconds=45,
    )
    assert round_0.id == "rnd_0"
    assert round_0.round_index == 0
    assert round_0.status == RoundStatus.PENDING.value
    assert round_0.duration_seconds == 45

    round_1 = create_quiz_round(
        memory_db,
        round_id="rnd_1",
        session_id="sess_303",
        round_index=1,
        duration_seconds=30,
    )
    assert round_1.id == "rnd_1"

    # Query by ID and index
    round_0_retrieved = get_quiz_round(memory_db, "rnd_0")
    assert round_0_retrieved is not None
    assert round_0_retrieved.id == "rnd_0"
    assert get_quiz_round(memory_db, "rnd_unknown") is None
    round_1_by_index = get_round_by_index(memory_db, "sess_303", 1)
    assert round_1_by_index is not None
    assert round_1_by_index.id == "rnd_1"
    assert get_round_by_index(memory_db, "sess_303", 99) is None

    # Update round status
    updated = update_quiz_round_status(
        memory_db,
        "rnd_0",
        status=RoundStatus.OPEN.value,
        opened_at="2026-09-05T08:01:00Z",
    )
    assert updated is True
    open_round = get_quiz_round(memory_db, "rnd_0")
    assert open_round is not None
    assert open_round.status == RoundStatus.OPEN.value

    # Close round
    update_quiz_round_status(
        memory_db,
        "rnd_0",
        status=RoundStatus.CLOSED.value,
        closed_at="2026-09-05T08:01:45Z",
    )
    closed = get_quiz_round(memory_db, "rnd_0")
    assert closed is not None
    assert closed.status == RoundStatus.CLOSED.value
    assert closed.closed_at == "2026-09-05T08:01:45Z"

    # List rounds
    all_rounds = list_rounds_for_session(memory_db, "sess_303")
    assert len(all_rounds) == 2
    assert all_rounds[0].id == "rnd_0"
    assert all_rounds[1].id == "rnd_1"


def test_session_creation_retrieval_failure_raises(memory_db, monkeypatch):
    import db.session_repository as repo

    monkeypatch.setattr(repo, "get_quiz_session", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match="Failed to retrieve newly created session"):
        create_quiz_session(memory_db, "fail_s", "Fail", "fail")


def test_round_creation_retrieval_failure_raises(memory_db, monkeypatch):
    import db.round_repository as repo

    create_quiz_session(memory_db, "sess_rf", "RF", "topic")
    monkeypatch.setattr(repo, "get_quiz_round", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match="Failed to retrieve created round"):
        create_quiz_round(memory_db, "fail_r", "sess_rf", 0)


def test_domain_exceptions_attributes():
    from session.exceptions import (
        InvalidOptionError,
        InvalidRoundStateError,
        InvalidSessionStateError,
        RoundNotFoundError,
        SessionNotFoundError,
        TransportError,
    )

    s_err = SessionNotFoundError("s_404")
    assert s_err.session_id == "s_404"
    assert "s_404" in str(s_err)

    r_err = RoundNotFoundError("r_404")
    assert r_err.round_id == "r_404"
    assert "r_404" in str(r_err)

    assert isinstance(InvalidSessionStateError("bad state"), Exception)
    assert isinstance(InvalidRoundStateError("round closed"), Exception)
    assert isinstance(InvalidOptionError("option X invalid"), Exception)
    assert isinstance(TransportError("network down"), Exception)
