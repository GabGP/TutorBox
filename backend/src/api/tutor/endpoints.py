"""Mode 2 endpoints: students chat with the Socratic math tutor, teachers watch.

The tutor answers only while the teacher has the class in `tutor` mode. Each turn
passes the gate (one at a time per login, a per-minute cap), is logged to
turn_logs with its SymPy target, and updates the teacher's roster.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.tutor.gate import TurnGate
from api.tutor.roster import TutorRoster
from api.tutor.schemas import (
    TutorMessageRequest,
    TutorReplyResponse,
    TutorRosterResponse,
    TutorStatusResponse,
    TutorStudent,
    TutorSummaryResponse,
)
from api.tutor.service import get_roster, get_turn_gate, get_tutor
from api.tutor.turn_logging import log_turn
from core.db.database import get_db
from core.db.mode_repository import get_mode
from core.security import AuthContext, require_roles
from modes.socratic import SocraticTutor

__all__ = ["router"]

router = APIRouter()

Caller = Annotated[AuthContext, Depends(require_roles("student", "teacher", "admin"))]
Staff = Annotated[AuthContext, Depends(require_roles("teacher", "admin"))]
Tutor = Annotated[SocraticTutor, Depends(get_tutor)]
Gate = Annotated[TurnGate, Depends(get_turn_gate)]
Roster = Annotated[TutorRoster, Depends(get_roster)]


@router.post("/message", response_model=TutorReplyResponse)
def send_message(
    payload: TutorMessageRequest, ctx: Caller, tutor: Tutor, gate: Gate, roster: Roster
) -> TutorReplyResponse:
    """One chat turn: the tutor's reply to what the child typed."""
    _require_tutor_mode()
    with gate.turn(ctx.session_id):
        result = tutor.respond(ctx.session_id, payload.message)
    log_turn(ctx.session_id, payload.message, result)
    if ctx.role == "student":
        problem = result.problem.text if result.problem else None
        solved = result.is_correct is True
        roster.record(ctx.user_id, ctx.username, problem, result.hint_level, solved)
    return TutorReplyResponse(
        reply=result.reply,
        kind=result.kind,
        hint_level=result.hint_level,
        used_model=result.used_model,
        topic=result.topic_id,
    )


@router.post("/reset", response_model=TutorStatusResponse)
def reset_conversation(
    ctx: Caller, tutor: Tutor, roster: Roster
) -> TutorStatusResponse:
    """Forgets the problem in progress; the turn history stays in turn_logs."""
    tutor.reset(ctx.session_id)
    if ctx.role == "student":
        roster.cleared(ctx.user_id, ctx.username)
    return TutorStatusResponse()


@router.post("/ping", response_model=TutorStatusResponse)
def ping(ctx: Caller, roster: Roster) -> TutorStatusResponse:
    """The chat is open: keeps the student 'connected' on the teacher's panel."""
    if ctx.role == "student":
        roster.seen(ctx.user_id, ctx.username)
    return TutorStatusResponse()


@router.get("/students", response_model=TutorRosterResponse)
def list_students(_ctx: Staff, roster: Roster) -> TutorRosterResponse:
    """Students using the tutor: connected ones first, then the last 30 minutes."""
    students = [TutorStudent.model_validate(row) for row in roster.snapshot()]
    return TutorRosterResponse(students=students)


@router.get("/summary", response_model=TutorSummaryResponse)
def summary(roster: Roster) -> TutorSummaryResponse:
    """Totals for the classroom screen, which has no login: counts only, no names."""
    rows = roster.snapshot()
    online = [row for row in rows if row["online"]]
    return TutorSummaryResponse(
        online=len(online),
        solved=sum(int(row["solved"]) for row in rows),
        need_help=sum(1 for row in online if row["problem"] and row["hint_level"] == 3),
    )


def _require_tutor_mode() -> None:
    with get_db() as conn:
        if get_mode(conn) != "tutor":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El tutor no está activo. Espera las instrucciones de tu "
                "maestra o maestro.",
            )
