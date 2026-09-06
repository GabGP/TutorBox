"""Participant and public observation endpoints for quiz sessions."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.session.schema import (
    CastVoteRequest,
    SessionStateResponse,
    VoteResponse,
)
from api.session.state_builder import build_session_state
from db.database import get_db
from db.round_repository import get_round_by_index
from db.session_repository import get_quiz_session
from security import AuthContext, get_current_session
from session.engine import QuizSessionEngine
from session.exceptions import (
    InvalidOptionError,
    InvalidRoundStateError,
    RoundNotFoundError,
    SessionNotFoundError,
    VoteAlreadyCastError,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{session_id}", response_model=SessionStateResponse)
def get_session_state(session_id: str) -> SessionStateResponse:
    """Retrieves current public match state and active question timer."""
    with get_db() as conn:
        engine = QuizSessionEngine(conn)
        return build_session_state(conn, session_id, engine)


@router.post("/{session_id}/vote", response_model=VoteResponse)
def submit_vote(
    session_id: str,
    payload: CastVoteRequest,
    ctx: Annotated[AuthContext, Depends(get_current_session)],
) -> VoteResponse:
    """Casts an immutable student vote with first-press lock enforcement."""
    with get_db() as conn:
        engine = QuizSessionEngine(conn)
        session = get_quiz_session(conn, session_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found.",
            )

        current_round = get_round_by_index(
            conn, session_id, session.current_round_index
        )
        if current_round is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active round not found.",
            )

        try:
            vote = engine.cast_vote(
                session_id,
                current_round.id,
                ctx.user_id,
                payload.selected_option,
                response_time_ms=payload.response_time_ms,
                transport_type=payload.transport_type,
                device_id=payload.device_id,
            )
            conn.commit()
        except VoteAlreadyCastError as err:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(err),
            ) from err
        except InvalidOptionError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err),
            ) from err
        except (
            InvalidRoundStateError,
            SessionNotFoundError,
            RoundNotFoundError,
        ) as err:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(err),
            ) from err

    return VoteResponse(
        vote_id=vote.id,
        session_id=vote.session_id,
        round_id=vote.round_id,
        student_id=vote.student_id,
        selected_option=vote.selected_option,
        recorded_at=vote.created_at,
    )
