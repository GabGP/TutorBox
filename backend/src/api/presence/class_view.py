"""GET /api/v1/presence/class: every student with the status of their phone and clicker.

Teachers and admins only. The rows come from the class roster and the store is read
through status.py, so the rules for online, dropped and absent live in one place.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from api.presence.schemas import (
    ClassPresenceResponse,
    ClickerPresence,
    PhonePresence,
    StudentPresence,
)
from api.presence.service import get_presence_store
from api.presence.status import (
    best_status,
    connection_status,
    signal_level,
)
from api.presence.store import PresenceStore, Sighting
from core.db.class_roster_repository import (
    ClassStudent,
    list_students_with_clickers,
    list_unassigned_clicker_ids,
)
from core.db.database import get_db
from core.security import AuthContext, require_roles

__all__ = ["router"]

router = APIRouter()

Staff = Annotated[AuthContext, Depends(require_roles("teacher", "admin"))]
Store = Annotated[PresenceStore, Depends(get_presence_store)]


@router.get("/class", response_model=ClassPresenceResponse)
def class_presence(_ctx: Staff, store: Store) -> ClassPresenceResponse:
    """The class as the teacher's lobby lists it, with the counts of online students."""
    with get_db() as conn:
        students = list_students_with_clickers(conn)
        unassigned_clickers = list_unassigned_clicker_ids(conn)
    rows = [_student_presence(student, store) for student in students]
    return ClassPresenceResponse(
        online=sum(1 for row in rows if row.status == "online"),
        total=len(rows),
        students=rows,
        unassigned_clickers=unassigned_clickers,
    )


def _student_presence(student: ClassStudent, store: PresenceStore) -> StudentPresence:
    phone = _phone_presence(store.phone(student.user_id))
    clicker = (
        None
        if student.device_id is None
        else _clicker_presence(student.device_id, store.clicker(student.device_id))
    )
    clicker_status = "absent" if clicker is None else clicker.status
    return StudentPresence(
        user_id=student.user_id,
        username=student.username,
        status=best_status(phone.status, clicker_status),
        phone=phone,
        clicker=clicker,
    )


def _phone_presence(sighting: Sighting | None) -> PhonePresence:
    return PhonePresence(
        status=connection_status(sighting),
        seconds_ago=_seconds_ago(sighting),
    )


def _clicker_presence(device_id: str, sighting: Sighting | None) -> ClickerPresence:
    """A clicker never heard from reports no vitals; a stopped one keeps its last."""
    if sighting is None:
        return ClickerPresence(
            device_id=device_id,
            status="absent",
            seconds_ago=None,
            signal=None,
            rssi=None,
            battery_pct=None,
        )
    return ClickerPresence(
        device_id=device_id,
        status=connection_status(sighting),
        seconds_ago=sighting.seconds_ago,
        signal=signal_level(sighting.rssi),
        rssi=sighting.rssi,
        battery_pct=sighting.battery_pct,
    )


def _seconds_ago(sighting: Sighting | None) -> int | None:
    return None if sighting is None else sighting.seconds_ago
