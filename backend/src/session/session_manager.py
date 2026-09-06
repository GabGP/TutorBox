"""Manages quiz session records, round provisioning, and match state advancement."""

import sqlite3
import time

from db.round_repository import create_quiz_round
from db.session_repository import (
    create_quiz_session,
    get_quiz_session,
    update_quiz_session_status,
)
from session.exceptions import (
    InvalidSessionStateError,
    SessionNotFoundError,
)
from session.models import QuizSessionRecord, SessionStatus


def initialize_quiz_session(
    conn: sqlite3.Connection,
    session_id: str,
    title: str,
    topic: str,
    question_ids: list[str],
    *,
    teacher_id: int | None = None,
    duration_seconds: int = 30,
) -> QuizSessionRecord:
    """Provisions a quiz session in lobby state with its constituent rounds."""
    session = create_quiz_session(
        conn,
        session_id,
        title,
        topic,
        teacher_id=teacher_id,
        question_count=len(question_ids),
    )
    for index, question_id in enumerate(question_ids):
        create_quiz_round(
            conn,
            f"{session_id}_r{index}",
            session_id,
            round_index=index,
            question_id=question_id,
            duration_seconds=duration_seconds,
        )
    return session


def activate_quiz_session(
    conn: sqlite3.Connection, session_id: str
) -> QuizSessionRecord:
    """Transitions a session from lobby to active state."""
    session = get_quiz_session(conn, session_id)
    if session is None:
        raise SessionNotFoundError(session_id)
    if session.status != SessionStatus.LOBBY.value:
        raise InvalidSessionStateError(f"Session '{session_id}' not in lobby.")

    update_quiz_session_status(
        conn,
        session_id,
        SessionStatus.ACTIVE.value,
        started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    updated = get_quiz_session(conn, session_id)
    return updated or session


def advance_quiz_session(conn: sqlite3.Connection, session_id: str) -> int | None:
    """Advances current round index or completes the session. Returns next index if any."""
    session = get_quiz_session(conn, session_id)
    if session is None:
        raise SessionNotFoundError(session_id)

    next_index = session.current_round_index + 1
    if next_index < session.question_count:
        update_quiz_session_status(
            conn, session_id, session.status, current_round_index=next_index
        )
        return next_index

    update_quiz_session_status(
        conn,
        session_id,
        SessionStatus.COMPLETED.value,
        ended_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    return None
