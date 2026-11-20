"""Teacher route that cancels a quiz match in the lobby or mid-game."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.session.schemas import SessionStateResponse
from api.session.state_builder import build_session_state
from core.db.database import get_db
from core.security import AuthContext, require_roles
from modes.quiz.session.engine import QuizSessionEngine
from modes.quiz.session.exceptions import (
    InvalidSessionStateError,
    SessionNotFoundError,
)

router = APIRouter()


@router.post("/{session_id}/abandon", response_model=SessionStateResponse)
def abandon_session(
    session_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
) -> SessionStateResponse:
    """Cancels the match: it leaves /current and its open round stops taking votes."""
    with get_db() as conn:
        engine = QuizSessionEngine(conn)
        try:
            engine.abandon_session(session_id)
            conn.commit()
        except SessionNotFoundError as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
            ) from err
        except InvalidSessionStateError as err:
            raise HTTPException(  # already completed or cancelled
                status_code=status.HTTP_409_CONFLICT, detail=str(err)
            ) from err
        return build_session_state(conn, session_id, engine)
