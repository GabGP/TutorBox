"""Mode 1 read endpoint: the teacher's weekly or monthly quiz report by topic."""

from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.db.database import get_db
from core.db.quiz_analytics import Period, QuizAnalytics, summarize_quiz_analytics
from core.security import AuthContext, require_roles

__all__ = ["router"]

router = APIRouter()

Day = Annotated[
    date | None,
    Query(alias="date", description="Any day in the period; defaults to today."),
]


@router.get("/analytics", response_model=QuizAnalytics)
def get_quiz_analytics(
    _: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    period: Period = "week",
    day: Day = None,
) -> QuizAnalytics:
    """Accuracy per topic, change vs the previous period, and top misconceptions."""
    with get_db() as conn:
        today = datetime.now(timezone.utc).date()  # votes are stamped in UTC
        return summarize_quiz_analytics(conn, period, day or today)
