"""Clicker check-in: the one call an ESP32 makes every second.

It enrolls a new clicker, saves its vitals for the teacher's fleet view, and answers
the only question the clicker's LED needs: is there a round my student can vote in?
"""

import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from api.clicker.credentials import (
    ClickerCredentials,
    authenticate_clicker,
    clicker_credentials,
)
from api.clicker.schemas import CheckinRequest, CheckinResponse
from core.db.clicker_repository import record_checkin
from core.db.database import get_db
from core.db.round_repository import get_round_by_index
from core.db.session_repository import get_current_quiz_session
from core.db.vote_repository import has_student_voted
from modes.quiz.session.engine import QuizSessionEngine
from modes.quiz.session.models import RoundStatus

logger = logging.getLogger(__name__)
router = APIRouter()


def current_round_view(
    conn: sqlite3.Connection, device_id: str, student_id: int | None
) -> CheckinResponse:
    """The current session's round as one clicker sees it.

    `round_open` is what the vote endpoint will accept: status open and, when the
    round has a countdown in memory, time left. `voted` covers votes from any
    transport, so a student who answered on a phone sees the clicker as done.
    """
    view = CheckinResponse(device_id=device_id, assigned=student_id is not None)
    session = get_current_quiz_session(conn)
    if session is None:
        return view
    round_record = get_round_by_index(conn, session.id, session.current_round_index)
    if round_record is None:
        return view
    remaining = QuizSessionEngine(conn).get_remaining_time(round_record.id)
    view.round_id = round_record.id
    view.round_open = round_record.status == RoundStatus.OPEN.value and (
        remaining is None or remaining > 0
    )
    view.voted = student_id is not None and has_student_voted(
        conn, round_record.id, student_id
    )
    return view


@router.post("/checkin", response_model=CheckinResponse)
def checkin(
    payload: CheckinRequest,
    creds: Annotated[ClickerCredentials, Depends(clicker_credentials)],
) -> CheckinResponse:
    """Enrolls on first contact, records vitals, and reports the open round."""
    with get_db() as conn:
        clicker = authenticate_clicker(conn, creds, enroll=True)
        record_checkin(
            conn,
            clicker.device_id,
            firmware=payload.firmware,
            rssi=payload.rssi,
            battery_mv=payload.battery_mv,
        )
        conn.commit()
        return current_round_view(conn, clicker.device_id, clicker.assigned_user_id)
