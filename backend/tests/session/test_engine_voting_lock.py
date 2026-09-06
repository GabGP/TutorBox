"""Unit tests for first-press voting locks and vote processing validation."""

import os
import sqlite3
import tempfile

import pytest
from session.engine import QuizSessionEngine
from session.exceptions import (
    InvalidOptionError,
    InvalidRoundStateError,
    RoundNotFoundError,
    VoteAlreadyCastError,
)

from db.migrations import apply_migrations
from db.quiz import create_question
from quiz.contracts.models import DistractorDetail, QuizQuestionCreate


@pytest.fixture
def voting_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    apply_migrations(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row

    # Seed users
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin, role) VALUES (1, 't1', 'h', 'teacher')"
    )
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin, role) VALUES (10, 's10', 'h', 'student')"
    )
    conn.execute(
        "INSERT INTO users (id, username, hashed_pin, role) VALUES (11, 's11', 'h', 'student')"
    )

    q = create_question(
        conn,
        QuizQuestionCreate(
            topic="arithmetic",
            subconcept="multiplication",
            question_text="Cuanto es 4 * 5?",
            options={"A": "20", "B": "9", "C": "25", "D": "16"},
            correct_option="A",
            distractors={
                "B": DistractorDetail(
                    misconception="added_addends", explanation="Sumaste."
                ),
                "C": DistractorDetail(
                    misconception="extra_group", explanation="Sumaste de mas."
                ),
                "D": DistractorDetail(
                    misconception="squared_first", explanation="Elevaste al cuadrado."
                ),
            },
        ),
    )
    conn.commit()

    yield conn, q

    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_first_press_lock_rejects_duplicate_vote(voting_db):
    conn, question_id = voting_db
    engine = QuizSessionEngine(conn)
    engine.create_session("sess_lock", "Lock Test", "arithmetic", [question_id])
    round_rec = engine.start_session("sess_lock")

    # First vote succeeds
    first_vote = engine.cast_vote("sess_lock", round_rec.id, 10, "A")
    assert first_vote.selected_option == "A"
    assert first_vote.is_correct is True

    # Second vote in the same round must raise VoteAlreadyCastError
    with pytest.raises(VoteAlreadyCastError, match="has already voted"):
        engine.cast_vote("sess_lock", round_rec.id, 10, "B")


def test_vote_with_invalid_option_fails(voting_db):
    conn, question_id = voting_db
    engine = QuizSessionEngine(conn)
    engine.create_session("sess_opt", "Option Test", "arithmetic", [question_id])
    round_rec = engine.start_session("sess_opt")

    with pytest.raises(InvalidOptionError, match="Invalid option"):
        engine.cast_vote("sess_opt", round_rec.id, 10, "E")


def test_vote_on_closed_round_fails(voting_db):
    conn, question_id = voting_db
    engine = QuizSessionEngine(conn)
    engine.create_session("sess_closed", "Closed Test", "arithmetic", [question_id])
    round_rec = engine.start_session("sess_closed")
    engine.close_round("sess_closed", round_rec.id)

    with pytest.raises(InvalidRoundStateError, match="not open"):
        engine.cast_vote("sess_closed", round_rec.id, 10, "A")


def test_vote_on_non_existent_round_fails(voting_db):
    conn, question_id = voting_db
    engine = QuizSessionEngine(conn)
    engine.create_session("sess_nonex", "NonEx Test", "arithmetic", [question_id])
    engine.start_session("sess_nonex")

    with pytest.raises(RoundNotFoundError):
        engine.cast_vote("sess_nonex", "invalid_round_id", 10, "A")


def test_vote_records_misconception_for_distractor(voting_db):
    conn, question_id = voting_db
    engine = QuizSessionEngine(conn)
    engine.create_session("sess_dist", "Distractor Test", "arithmetic", [question_id])
    round_rec = engine.start_session("sess_dist")

    wrong_vote = engine.cast_vote("sess_dist", round_rec.id, 11, "B")
    assert wrong_vote.selected_option == "B"
    assert wrong_vote.is_correct is False
    assert wrong_vote.misconception == "added_addends"


def test_vote_on_expired_timer(voting_db):
    conn, question_id = voting_db
    engine = QuizSessionEngine(conn)
    engine.create_session("sess_exp", "Expire Test", "arithmetic", [question_id])
    round_rec = engine.start_session("sess_exp")

    timer = engine._timers[round_rec.id]
    timer.stop()  # Forces expiration

    with pytest.raises(InvalidRoundStateError, match="expired"):
        engine.cast_vote("sess_exp", round_rec.id, 10, "A")


def test_vote_on_round_without_question(voting_db):
    conn, _ = voting_db
    engine = QuizSessionEngine(conn)
    from db.round_repository import create_quiz_round
    from db.session_repository import create_quiz_session

    create_quiz_session(conn, "s_no_q", "No Q", "topic", question_count=1)
    round_no_q = create_quiz_round(conn, "r_no_q", "s_no_q", 0, question_id=None)
    engine.open_round("s_no_q", 0)

    vote = engine.cast_vote("s_no_q", round_no_q.id, 10, "A")
    assert vote.is_correct is False
    assert vote.misconception is None


def test_vote_on_round_with_missing_question_in_db(voting_db):
    conn, question_id = voting_db
    engine = QuizSessionEngine(conn)
    from db.quiz import soft_delete_question

    engine.create_session("s_del_q", "Deleted Q", "arithmetic", [question_id])
    round_rec = engine.start_session("s_del_q")

    # Soft delete the question
    soft_delete_question(conn, question_id)
    conn.commit()

    vote = engine.cast_vote("s_del_q", round_rec.id, 10, "A")
    assert vote.is_correct is False
    assert vote.misconception is None
