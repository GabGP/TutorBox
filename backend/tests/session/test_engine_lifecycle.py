"""Unit tests for the QuizSessionEngine match lifecycle and state transitions."""

import os
import sqlite3
import tempfile
from typing import Any

import pytest

from db.migrations import apply_migrations
from db.quiz import create_question
from quiz.contracts.models import DistractorDetail, QuizQuestionCreate
from session.engine import QuizSessionEngine
from session.exceptions import (
    InvalidRoundStateError,
    InvalidSessionStateError,
    RoundNotFoundError,
    SessionNotFoundError,
)
from session.models import RoundStatus, SessionStatus


@pytest.fixture
def session_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    apply_migrations(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row

    # Seed teacher and sample questions
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin, role) VALUES (1, 'teacher', 'hash', 'teacher')"
    )
    q1 = create_question(
        conn,
        QuizQuestionCreate(
            topic="arithmetic",
            subconcept="addition",
            question_text="Cuanto es 2 + 2?",
            options={"A": "4", "B": "5", "C": "3", "D": "6"},
            correct_option="A",
            distractors={
                "B": DistractorDetail(
                    misconception="off_by_one", explanation="Sumaste uno de mas."
                ),
                "C": DistractorDetail(
                    misconception="off_by_one_minus",
                    explanation="Sumaste uno de menos.",
                ),
                "D": DistractorDetail(
                    misconception="doubled_addend", explanation="Duplicaste el sumando."
                ),
            },
        ),
    )
    q2 = create_question(
        conn,
        QuizQuestionCreate(
            topic="arithmetic",
            subconcept="multiplication",
            question_text="Cuanto es 3 * 3?",
            options={"A": "6", "B": "9", "C": "12", "D": "15"},
            correct_option="B",
            distractors={
                "A": DistractorDetail(
                    misconception="added_not_multiplied", explanation="Sumaste 3 + 3."
                ),
                "C": DistractorDetail(
                    misconception="extra_multiple", explanation="Multiplicaste por 4."
                ),
                "D": DistractorDetail(
                    misconception="arbitrary", explanation="Calculo incorrecto."
                ),
            },
        ),
    )
    conn.commit()

    yield conn, [q1, q2]

    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_create_session_and_provision_rounds(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)

    session = engine.create_session(
        "s1", "Quiz 1", "arithmetic", question_ids, teacher_id=1
    )

    assert session.id == "s1"
    assert session.status == SessionStatus.LOBBY.value
    assert session.question_count == 2
    assert session.current_round_index == 0


def test_start_session_lifecycle(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)
    engine.create_session("s2", "Quiz 2", "arithmetic", question_ids)

    round_0 = engine.start_session("s2")

    assert round_0.round_index == 0
    assert round_0.status == RoundStatus.OPEN.value
    assert round_0.opened_at is not None


def test_start_session_errors(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)

    with pytest.raises(SessionNotFoundError):
        engine.start_session("non_existent")

    engine.create_session("s3", "Quiz 3", "arithmetic", question_ids)
    engine.start_session("s3")

    with pytest.raises(InvalidSessionStateError):
        engine.start_session("s3")


def test_round_transitions_and_reveal(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)
    engine.create_session("s4", "Quiz 4", "arithmetic", question_ids)
    round_0 = engine.start_session("s4")

    # Vote then reveal (auto-closes open round)
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin) VALUES (10, 'st10', 'hash')"
    )
    conn.commit()
    engine.cast_vote("s4", round_0.id, 10, "A")

    tally, decision = engine.reveal_round("s4", round_0.id)
    assert tally.total_votes == 1
    assert tally.correct_count == 1
    assert decision.should_speak is False
    assert decision.reason == "majority_correct"


def test_next_round_and_session_completion(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)
    engine.create_session("s5", "Quiz 5", "arithmetic", question_ids)
    engine.start_session("s5")

    # Advance to round 1
    round_1 = engine.next_round("s5")
    assert round_1 is not None
    assert round_1.round_index == 1
    assert round_1.status == RoundStatus.OPEN.value

    # Advance past last round completes session
    completed = engine.next_round("s5")
    assert completed is None


def test_event_listener_hook_dispatch(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)
    events: list[tuple[str, dict[str, Any]]] = []

    engine.add_event_listener(lambda name, payload: events.append((name, payload)))

    engine.create_session("s6", "Quiz 6", "arithmetic", question_ids)
    round_0 = engine.start_session("s6")

    conn.execute(
        "INSERT INTO users (id, username, hashed_pin) VALUES (20, 'st20', 'hash')"
    )
    conn.commit()
    engine.cast_vote("s6", round_0.id, 20, "B")
    engine.close_round("s6", round_0.id)
    engine.reveal_round("s6", round_0.id)
    engine.next_round("s6")
    engine.next_round("s6")

    event_names = [event[0] for event in events]
    assert "round_opened" in event_names
    assert "vote_cast" in event_names
    assert "round_closed" in event_names
    assert "round_revealed" in event_names
    assert "session_completed" in event_names


def test_round_state_errors(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)
    engine.create_session("s7", "Quiz 7", "arithmetic", question_ids)

    with pytest.raises(RoundNotFoundError):
        engine.open_round("s7", 99)

    engine.start_session("s7")
    with pytest.raises(InvalidRoundStateError):
        engine.open_round("s7", 0)

    with pytest.raises(RoundNotFoundError):
        engine.close_round("s7", "bad_round_id")

    with pytest.raises(RoundNotFoundError):
        engine.reveal_round("s7", "bad_round_id")


def test_session_and_round_additional_error_branches(session_db):
    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)

    # Advance nonexistent session
    with pytest.raises(SessionNotFoundError):
        engine.next_round("nonexistent_session")

    # Close round when not open (already closed)
    engine.create_session("s8", "Quiz 8", "arithmetic", question_ids)
    round_0 = engine.start_session("s8")
    engine.close_round("s8", round_0.id)
    with pytest.raises(InvalidRoundStateError, match="not open"):
        engine.close_round("s8", round_0.id)

    # Reveal round when still pending (round 1 of s8 is still pending)
    from db.round_repository import get_round_by_index

    round_1 = get_round_by_index(conn, "s8", 1)
    assert round_1 is not None
    with pytest.raises(InvalidRoundStateError, match="cannot be revealed"):
        engine.reveal_round("s8", round_1.id)


def test_get_remaining_time_and_reset_state(session_db):
    from session.engine import reset_shared_session_state

    conn, question_ids = session_db
    engine = QuizSessionEngine(conn)
    engine.create_session("s_rem", "Quiz Rem", "arithmetic", question_ids)

    assert engine.get_remaining_time("nonexistent_round") is None

    round_rec = engine.open_round("s_rem", 0)
    rem = engine.get_remaining_time(round_rec.id)
    assert rem is not None and rem > 0.0

    engine.close_round("s_rem", round_rec.id)
    assert engine.get_remaining_time(round_rec.id) is None

    reset_shared_session_state()
