"""Classroom mode switch: the teacher's phone is the remote for a keyboard-less appliance.

GET is public so the classroom screen (/pantalla/) and student phones can poll it before
login. PUT is staff-only. Switching away from the quiz is refused while a round is live.
"""

import logging
import threading
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.db.audit import record_audit
from core.db.database import get_db
from core.db.mode_repository import ApplianceMode, get_mode, set_mode
from core.db.session_repository import get_current_quiz_session
from core.llm.residency import (
    ModelResidencyManager,
    ModelResidencyResult,
    get_model_residency,
)
from core.security import AuthContext, require_roles
from modes.quiz.session.models import SessionStatus

logger = logging.getLogger(__name__)
router = APIRouter()
# Two quick switches end in the state of the last one: each saves the mode and moves the
# tutor model in one step, so the two can never interleave.
_mode_change_lock = threading.Lock()


class ModeState(BaseModel):
    mode: ApplianceMode


class ModeChangeResponse(BaseModel):
    mode: ApplianceMode
    model: ModelResidencyResult


@router.get("", response_model=ModeState)
def read_mode() -> ModeState:
    """Returns the classroom-wide active mode."""
    with get_db() as conn:
        return ModeState(mode=get_mode(conn))


@router.put("", response_model=ModeChangeResponse)
def change_mode(
    payload: ModeState,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    residency: Annotated[ModelResidencyManager, Depends(get_model_residency)],
) -> ModeChangeResponse:
    """Sets the active mode for every screen, then loads or unloads the tutor model."""
    with _mode_change_lock:
        with get_db() as conn:
            current = get_current_quiz_session(conn)
            if (
                payload.mode != "quiz"
                and current is not None
                and current.status == SessionStatus.ACTIVE.value
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Termina el juego antes de cambiar de modo.",
                )
            set_mode(conn, payload.mode, ctx.user_id)
            record_audit(conn, actor_user_id=ctx.user_id, action="mode_changed")
            conn.commit()
        model = residency.apply_mode(payload.mode)
    logger.info("Appliance mode set to '%s' by '%s'.", payload.mode, ctx.username)
    return ModeChangeResponse(mode=payload.mode, model=model)
