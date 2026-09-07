"""State presentation builder for quiz session API endpoints."""

import sqlite3

from fastapi import HTTPException, status

from api.session.schemas import SessionRoundInfo, SessionStateResponse
from core.db.round_repository import get_round_by_index
from core.db.session_repository import get_quiz_session
from modes.quiz.session.engine import QuizSessionEngine

__all__ = ["build_session_state"]


def build_session_state(
    conn: sqlite3.Connection, session_id: str, engine: QuizSessionEngine
) -> SessionStateResponse:
    """Constructs a SessionStateResponse using public engine queries."""
    session = get_quiz_session(conn, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    current_round = get_round_by_index(conn, session_id, session.current_round_index)
    round_info: SessionRoundInfo | None = None
    if current_round:
        time_rem = engine.get_remaining_time(current_round.id)
        round_info = SessionRoundInfo(
            round_id=current_round.id,
            round_index=current_round.round_index,
            status=current_round.status,
            question_id=current_round.question_id,
            duration_seconds=current_round.duration_seconds,
            time_remaining=time_rem,
        )

    return SessionStateResponse(
        id=session.id,
        title=session.title,
        topic=session.topic,
        status=session.status,
        current_round_index=session.current_round_index,
        question_count=session.question_count,
        current_round=round_info,
    )
