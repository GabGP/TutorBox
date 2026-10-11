"""Clicker votes: the hardware transport into the same session engine as phones.

The web endpoint (api/session/participant.py) records every vote as transport "web";
this is the only path that records "hardware", and only for an authenticated clicker
that a teacher assigned to a student. The first-press lock is shared, so a student
who already answered on a phone gets 409 here, and the other way round.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.clicker.credentials import (
    ClickerCredentials,
    authenticate_clicker,
    clicker_credentials,
)
from api.clicker.schemas import ClickerVoteRequest, ClickerVoteResponse
from core.db.database import get_db
from core.db.round_repository import get_quiz_round
from modes.quiz.session.engine import QuizSessionEngine
from modes.quiz.session.exceptions import (
    InvalidRoundStateError,
    RoundNotFoundError,
    VoteAlreadyCastError,
)
from modes.quiz.session.models import TransportType

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/vote", response_model=ClickerVoteResponse)
def clicker_vote(
    payload: ClickerVoteRequest,
    creds: Annotated[ClickerCredentials, Depends(clicker_credentials)],
) -> ClickerVoteResponse:
    """Records the assigned student's vote for the round the clicker saw open."""
    with get_db() as conn:
        clicker = authenticate_clicker(conn, creds, enroll=False)
        if clicker.assigned_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Clicker is not assigned to any student.",
            )
        round_record = get_quiz_round(conn, payload.round_id)
        if round_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Round not found."
            )
        try:
            vote = QuizSessionEngine(conn).cast_vote(
                round_record.session_id,
                round_record.id,
                clicker.assigned_user_id,
                payload.selected_option,
                response_time_ms=payload.response_time_ms,
                transport_type=TransportType.HARDWARE.value,
                device_id=clicker.device_id,
            )
            conn.commit()
        except (
            VoteAlreadyCastError,
            InvalidRoundStateError,
            RoundNotFoundError,
        ) as err:
            # Already voted, round closed or timed out: final, the clicker shows red.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(err)
            ) from err

    logger.info("Clicker %s voted in round %s.", clicker.device_id, vote.round_id)
    return ClickerVoteResponse(
        vote_id=vote.id,
        round_id=vote.round_id,
        selected_option=vote.selected_option,
        recorded_at=vote.created_at,
    )
