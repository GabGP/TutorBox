"""Teacher and host management endpoints for quiz sessions."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.session.dependencies import get_session_and_current_round
from api.session.schemas import (
    CreateSessionRequest,
    RoundRevealResponse,
    SessionStateResponse,
)
from api.session.state_builder import build_session_state
from core.db.database import get_db
from core.security import AuthContext, require_roles
from modes.quiz.session.engine import QuizSessionEngine
from modes.quiz.session.exceptions import (
    InvalidRoundStateError,
    InvalidSessionStateError,
    RoundNotFoundError,
    SessionNotFoundError,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/", response_model=SessionStateResponse, status_code=status.HTTP_201_CREATED
)
def create_session(
    payload: CreateSessionRequest,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
) -> SessionStateResponse:
    """Creates a new quiz session in lobby state."""
    session_id = f"s_{uuid.uuid4().hex[:12]}"
    with get_db() as conn:
        engine = QuizSessionEngine(conn)
        engine.create_session(
            session_id,
            payload.title,
            payload.topic,
            payload.question_ids,
            teacher_id=ctx.user_id,
            duration_seconds=payload.duration_seconds,
        )
        conn.commit()
        return build_session_state(conn, session_id, engine)


@router.post("/{session_id}/start", response_model=SessionStateResponse)
def start_session(
    session_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
) -> SessionStateResponse:
    """Transitions a session from lobby to active and opens the initial round."""
    with get_db() as conn:
        engine = QuizSessionEngine(conn)
        try:
            engine.start_session(session_id)
            conn.commit()
        except (SessionNotFoundError, RoundNotFoundError) as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
            ) from err
        except InvalidSessionStateError as err:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(err)
            ) from err
        return build_session_state(conn, session_id, engine)


@router.post("/{session_id}/close", response_model=SessionStateResponse)
def close_round(
    session_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
) -> SessionStateResponse:
    """Closes the active round's voting window."""
    with get_db() as conn:
        engine = QuizSessionEngine(conn)
        _, current_round = get_session_and_current_round(conn, session_id)
        try:
            engine.close_round(session_id, current_round.id)
            conn.commit()
        except InvalidRoundStateError as err:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(err)
            ) from err
        return build_session_state(conn, session_id, engine)


@router.post("/{session_id}/reveal", response_model=RoundRevealResponse)
def reveal_round(
    session_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
) -> RoundRevealResponse:
    """Reveals the round outcome, aggregates votes, and computes pedagogical decision."""
    with get_db() as conn:
        engine = QuizSessionEngine(conn)
        _, current_round = get_session_and_current_round(conn, session_id)
        try:
            tally, decision = engine.reveal_round(session_id, current_round.id)
            conn.commit()
        except InvalidRoundStateError as err:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(err)
            ) from err
    return RoundRevealResponse(
        round_id=current_round.id, tally=tally, decision=decision
    )


@router.post("/{session_id}/next", response_model=SessionStateResponse)
def next_round(
    session_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
) -> SessionStateResponse:
    """Advances to the next question round or completes the session."""
    with get_db() as conn:
        engine = QuizSessionEngine(conn)
        try:
            engine.next_round(session_id)
            conn.commit()
        except SessionNotFoundError as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
            ) from err
        return build_session_state(conn, session_id, engine)
