"""Mode 3 read endpoint: staff count the game events the appliance has stored.

It answers the question of the sync test: did every answer of this phone arrive,
once each? Filter by the phone's install id and compare the count with the phone's.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from api.games.schemas import GameEventSummaryResponse
from core.db.database import get_db
from core.db.game_event_summary import summarize_game_events
from core.security import AuthContext, require_roles
from modes.games import CLIENT_ID_PATTERN

__all__ = ["router"]

router = APIRouter()

InstallId = Annotated[
    str | None,
    Query(pattern=CLIENT_ID_PATTERN, description="Count one phone's events only."),
]


@router.get("/events/summary", response_model=GameEventSummaryResponse)
def get_events_summary(
    _: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    install_id: InstallId = None,
) -> GameEventSummaryResponse:
    """Counts the stored answers in total and per lesson."""
    with get_db() as conn:
        summary = summarize_game_events(conn, install_id=install_id)
    return GameEventSummaryResponse.model_validate(summary)
