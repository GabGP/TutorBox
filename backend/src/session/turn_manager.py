"""Manages question round transitions, timers, and pedagogical reveal decisions."""

import sqlite3
import time

from db.quiz import get_question_by_id
from db.round_repository import (
    get_quiz_round,
    get_round_by_index,
    update_quiz_round_status,
)
from db.vote_repository import get_votes_for_round
from session.aggregator import compute_round_tally
from session.evaluator import evaluate_turn_decision
from session.exceptions import (
    InvalidRoundStateError,
    RoundNotFoundError,
)
from session.models import (
    QuizRoundRecord,
    RoundStatus,
    RoundTally,
    TurnDecision,
)
from session.timer import RoundTimer


def open_turn_round(
    conn: sqlite3.Connection,
    timers: dict[str, RoundTimer],
    session_id: str,
    round_index: int,
) -> QuizRoundRecord:
    """Transitions a pending round to open and activates its countdown timer."""
    round_record = get_round_by_index(conn, session_id, round_index)
    if round_record is None:
        raise RoundNotFoundError(f"session={session_id}, index={round_index}")
    if round_record.status != RoundStatus.PENDING.value:
        raise InvalidRoundStateError(f"Round already {round_record.status}.")

    timer = RoundTimer(round_record.duration_seconds)
    timer.start()
    timers[round_record.id] = timer

    update_quiz_round_status(
        conn,
        round_record.id,
        RoundStatus.OPEN.value,
        opened_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    return get_quiz_round(conn, round_record.id) or round_record


def close_turn_round(
    conn: sqlite3.Connection,
    timers: dict[str, RoundTimer],
    round_id: str,
) -> QuizRoundRecord:
    """Closes an active voting window and stops its countdown timer."""
    round_record = get_quiz_round(conn, round_id)
    if round_record is None:
        raise RoundNotFoundError(round_id)
    if round_record.status != RoundStatus.OPEN.value:
        raise InvalidRoundStateError(f"Round '{round_id}' is not open.")

    timer = timers.pop(round_id, None)
    if timer:
        timer.stop()

    update_quiz_round_status(
        conn,
        round_id,
        RoundStatus.CLOSED.value,
        closed_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    return get_quiz_round(conn, round_id) or round_record


def reveal_turn_round(
    conn: sqlite3.Connection,
    timers: dict[str, RoundTimer],
    round_id: str,
) -> tuple[RoundTally, TurnDecision]:
    """Computes round tallies and evaluates the deterministic >51% Rule."""
    round_record = get_quiz_round(conn, round_id)
    if round_record is None:
        raise RoundNotFoundError(round_id)

    if round_record.status == RoundStatus.OPEN.value:
        round_record = close_turn_round(conn, timers, round_id)
    elif round_record.status not in (
        RoundStatus.CLOSED.value,
        RoundStatus.REVEALED.value,
    ):
        raise InvalidRoundStateError(f"Round '{round_id}' cannot be revealed.")

    question = (
        get_question_by_id(conn, round_record.question_id)
        if round_record.question_id
        else None
    )
    correct_option = question.correct_option if question else "A"
    distractors = question.distractors if question else None

    votes = get_votes_for_round(conn, round_id)
    tally = compute_round_tally(votes, correct_option)
    decision = evaluate_turn_decision(tally, distractors)

    update_quiz_round_status(conn, round_id, RoundStatus.REVEALED.value)
    return tally, decision
