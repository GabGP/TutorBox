"""Mode 3 endpoint: phones hand in the answers tapped in the grade apps.

Open in every class mode and without a login, because a phone sends its queue
whenever it reaches the appliance. Every event id is stored once; a repeated
delivery is counted as a duplicate.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from api.games.identity import optional_student_id
from api.games.schemas import GameEventBatch, GameEventBatchResult
from core.db.database import get_db
from modes.games import ACCEPTED, DUPLICATE, REJECTED, ingest_events

__all__ = ["router"]

router = APIRouter()

StudentId = Annotated[int | None, Depends(optional_student_id)]


@router.post("/events", response_model=GameEventBatchResult)
def receive_events(
    batch: GameEventBatch, student_id: StudentId
) -> GameEventBatchResult:
    """Stores the new events of a batch and reports each event's status."""
    with get_db() as conn:
        statuses = ingest_events(conn, batch.install_id, student_id, batch.events)
        conn.commit()
    return GameEventBatchResult(
        accepted=statuses.count(ACCEPTED),
        duplicates=statuses.count(DUPLICATE),
        rejected=statuses.count(REJECTED),
        results=statuses,
    )
