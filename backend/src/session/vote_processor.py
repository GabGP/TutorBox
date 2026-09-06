"""Processes student vote submissions, validation, and first-press locks."""

import sqlite3
import uuid

from db.question_repository import get_question_by_id
from db.round_repository import get_quiz_round
from db.vote_repository import record_student_vote
from session.exceptions import (
    InvalidOptionError,
    InvalidRoundStateError,
    RoundNotFoundError,
)
from session.models import (
    VALID_OPTIONS,
    QuizRoundRecord,
    RoundStatus,
    StudentVoteRecord,
)
from session.timer import RoundTimer


def _resolve_option_outcome(
    conn: sqlite3.Connection,
    round_record: QuizRoundRecord,
    selected_option: str,
) -> tuple[bool, str | None]:
    """Determines whether chosen option is correct and extracts misconception slug."""
    if not round_record.question_id:
        return False, None

    question = get_question_by_id(conn, round_record.question_id)
    if question is None:
        return False, None

    is_correct = selected_option == question.correct_option
    misconception: str | None = None
    if not is_correct and selected_option in question.distractors:
        misconception = question.distractors[selected_option].misconception

    return is_correct, misconception


def process_student_vote(
    conn: sqlite3.Connection,
    session_id: str,
    round_id: str,
    student_id: int,
    selected_option: str,
    *,
    timer: RoundTimer | None = None,
    response_time_ms: float | None = None,
    transport_type: str = "web",
    device_id: str | None = None,
) -> StudentVoteRecord:
    """Validates voting conditions, enforces first-press lock, and persists vote."""
    if selected_option not in VALID_OPTIONS:
        raise InvalidOptionError(f"Invalid option: '{selected_option}'.")

    round_record = get_quiz_round(conn, round_id)
    if round_record is None:
        raise RoundNotFoundError(round_id)
    if round_record.status != RoundStatus.OPEN.value:
        raise InvalidRoundStateError(f"Round '{round_id}' is not open.")

    if timer and timer.is_expired():
        raise InvalidRoundStateError("Voting window has expired.")

    is_correct, misconception = _resolve_option_outcome(
        conn, round_record, selected_option
    )

    return record_student_vote(
        conn,
        f"v_{uuid.uuid4().hex[:12]}",
        session_id,
        round_id,
        student_id,
        selected_option,
        is_correct=is_correct,
        misconception=misconception,
        transport_type=transport_type,
        device_id=device_id,
        response_time_ms=response_time_ms,
    )
