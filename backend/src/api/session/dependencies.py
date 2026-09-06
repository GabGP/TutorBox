"""Entity resolution dependencies for session API routes."""

import sqlite3

from fastapi import HTTPException, status

from db.round_repository import get_round_by_index
from db.session_repository import get_quiz_session
from session.models import QuizRoundRecord, QuizSessionRecord


def get_session_and_current_round(
    conn: sqlite3.Connection,
    session_id: str,
    round_not_found_detail: str = "Round not found.",
) -> tuple[QuizSessionRecord, QuizRoundRecord]:
    """Retrieves session and its active round, raising HTTP 404 if missing."""
    session = get_quiz_session(conn, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    current_round = get_round_by_index(conn, session_id, session.current_round_index)
    if current_round is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=round_not_found_detail,
        )
    return session, current_round
