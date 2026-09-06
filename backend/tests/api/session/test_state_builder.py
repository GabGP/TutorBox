"""Unit tests for the state_builder presentation helper."""

import os
import sqlite3
import tempfile

import pytest
from fastapi import HTTPException

from api.session.state_builder import build_session_state
from core.db.migrations import apply_migrations
from core.db.question_repository import create_question
from quiz.contracts.models import DistractorDetail, QuizQuestionCreate
from session.engine import QuizSessionEngine, reset_shared_session_state


@pytest.fixture
def session_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    apply_migrations(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Seed teacher and a question
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin, role) VALUES (1, 'teacher', 'hash', 'teacher')"
    )
    q1 = create_question(
        conn,
        QuizQuestionCreate(
            topic="arithmetic",
            subconcept="addition",
            question_text="1 + 1?",
            options={"A": "2", "B": "3", "C": "4", "D": "0"},
            correct_option="A",
            distractors={
                "B": DistractorDetail(
                    misconception="plus_one", explanation="Sumaste uno de mas."
                ),
                "C": DistractorDetail(
                    misconception="plus_two", explanation="Sumaste dos de mas."
                ),
                "D": DistractorDetail(
                    misconception="zero", explanation="Colocaste valor cero."
                ),
            },
        ),
    )
    conn.commit()

    yield conn, [q1]

    conn.close()
    if os.path.exists(db_path):
        os.unlink(db_path)
    reset_shared_session_state()


def test_build_session_state_missing_session_raises_404(session_db):
    conn, _ = session_db
    engine = QuizSessionEngine(conn)
    with pytest.raises(HTTPException) as exc_info:
        build_session_state(conn, "nonexistent_session", engine)
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_build_session_state_with_active_round(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)
    session = engine.create_session("s_builder", "Title", "arithmetic", question_ids)
    assert session.status == "lobby"

    # In lobby, round 0 is pending
    state_lobby = build_session_state(conn, "s_builder", engine)
    assert state_lobby.id == "s_builder"
    assert state_lobby.current_round is not None
    assert state_lobby.current_round.status == "pending"
    assert state_lobby.current_round.time_remaining is None

    # Start session -> round 0 opens
    engine.start_session("s_builder")
    state_active = build_session_state(conn, "s_builder", engine)

    assert state_active.status == "active"
    assert state_active.current_round is not None
    assert state_active.current_round.status == "open"
    assert state_active.current_round.time_remaining is not None
    assert state_active.current_round.time_remaining > 0.0
