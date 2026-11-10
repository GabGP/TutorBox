"""Mode 2 read endpoint: the teacher's daily, weekly or monthly tutor report."""

from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.db.database import get_db
from core.db.periods import Period
from core.db.tutor_analytics import TutorAnalytics, summarize_tutor_analytics
from core.security import AuthContext, require_roles

__all__ = ["router"]

router = APIRouter()

Day = Annotated[
    date | None,
    Query(alias="date", description="Any day in the period; defaults to today."),
]


@router.get("/analytics", response_model=TutorAnalytics)
def get_tutor_analytics(
    _: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    period: Period = "week",
    day: Day = None,
) -> TutorAnalytics:
    """Topics asked about and stuck on, plus one topic summary per student login."""
    with get_db() as conn:
        today = datetime.now(timezone.utc).date()  # turns are stamped in UTC
        return summarize_tutor_analytics(conn, period, day or today)
