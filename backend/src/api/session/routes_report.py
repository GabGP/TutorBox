"""Reporting and aggregate telemetry endpoints for quiz sessions."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.session.schema import SessionReportResponse
from db.database import get_db
from db.session_repository import get_quiz_session
from security import AuthContext, require_roles

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
        cursor = conn.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END), 0)
            FROM quiz_session_votes WHERE session_id = ?
            """,
            (session_id,),
        )
        total_votes, correct_votes = cursor.fetchone()
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
