"""Reporting and aggregate telemetry endpoints for quiz sessions."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.session.schemas import SessionReportResponse
from core.db.database import get_db
from core.db.session_repository import get_quiz_session
from core.db.vote_repository import get_session_vote_summary
from core.security import AuthContext, require_roles

router = APIRouter()


@router.get("/{session_id}/report", response_model=SessionReportResponse)
def get_session_report(
    session_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
) -> SessionReportResponse:
    """Computes summary statistics and accuracy percentage for a quiz match."""
    with get_db() as conn:
        session = get_quiz_session(conn, session_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found.",
            )
        total_votes, correct_votes = get_session_vote_summary(conn, session_id)
        accuracy = (
            round((correct_votes / total_votes) * 100, 2) if total_votes > 0 else 0.0
        )

    return SessionReportResponse(
        session_id=session.id,
        title=session.title,
        topic=session.topic,
        status=session.status,
        total_rounds=session.question_count,
        total_votes_cast=total_votes,
        average_accuracy_percentage=accuracy,
    )
