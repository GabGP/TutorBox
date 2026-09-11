"""Unit tests for the state_builder presentation helper."""

import os
import sqlite3
import tempfile

import pytest
from fastapi import HTTPException

from api.session.state_builder import build_session_state
from core.db.migrations import apply_migrations
from core.db.question_repository import create_question
from modes.quiz.contracts.models import DistractorDetail, QuizQuestionCreate
from modes.quiz.session.engine import QuizSessionEngine, reset_shared_session_state


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


def test_question_hidden_in_lobby_and_visible_once_open(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)
    engine.create_session("s_view", "Title", "arithmetic", question_ids)

    lobby = build_session_state(conn, "s_view", engine).current_round
    assert lobby is not None
    assert lobby.question is None and lobby.result is None and lobby.votes_cast == 0

    engine.start_session("s_view")
    opened = build_session_state(conn, "s_view", engine).current_round
    assert opened is not None and opened.question is not None
    assert opened.question.question_text == "1 + 1?"
    assert opened.question.options == {"A": "2", "B": "3", "C": "4", "D": "0"}
    assert opened.result is None
    # The answer must not leak anywhere in the public payload while voting is open.
    assert "correct_option" not in opened.model_dump_json()


def test_votes_cast_and_result_after_reveal(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin, role) "
        "VALUES (7, 'kid', 'hash', 'student')"
    )
    engine.create_session("s_res", "Title", "arithmetic", question_ids)
    engine.start_session("s_res")
    round_id = "s_res_r0"
    engine.cast_vote("s_res", round_id, 7, "B")

    voting = build_session_state(conn, "s_res", engine).current_round
    assert voting is not None and voting.votes_cast == 1 and voting.result is None

    engine.close_round("s_res", round_id)
    tally, decision = engine.reveal_round("s_res", round_id)
    revealed = build_session_state(conn, "s_res", engine).current_round
    assert revealed is not None and revealed.status == "revealed"
    assert revealed.result is not None
    # Read-only recompute matches exactly what POST /reveal returned.
    assert revealed.result.tally == tally
    assert revealed.result.decision == decision
    assert revealed.result.tally.correct_option == "A"
    assert revealed.result.tally.counts == {"A": 0, "B": 1, "C": 0, "D": 0}
    assert revealed.result.decision.should_speak is True
    assert revealed.result.explanations == {
        "B": "Sumaste uno de mas.",
        "C": "Sumaste dos de mas.",
        "D": "Colocaste valor cero.",
    }
    assert revealed.question is not None  # still shown alongside the result


def test_deleted_question_yields_no_question_view(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)
    engine.create_session("s_gone", "Title", "arithmetic", question_ids)
    engine.start_session("s_gone")
    conn.execute(
        "UPDATE quiz_questions SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
        (question_ids[0],),
    )
    info = build_session_state(conn, "s_gone", engine).current_round
    assert info is not None and info.status == "open"
    assert info.question is None and info.result is None
