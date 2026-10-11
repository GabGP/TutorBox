"""POST /api/v1/presence/heartbeat: a phone or a clicker says it is still connected."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.presence.schemas import HeartbeatRequest
from api.presence.service import get_presence_store
from api.presence.store import PresenceStore
from core.security import AuthContext, get_voter_session

__all__ = ["router"]

router = APIRouter()

Voter = Annotated[AuthContext, Depends(get_voter_session)]
Store = Annotated[PresenceStore, Depends(get_presence_store)]


@router.post("/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
def heartbeat(
    ctx: Voter, store: Store, payload: HeartbeatRequest | None = None
) -> None:
    """Records that the caller is connected. The body is optional.

    A clicker's beat is recorded with the vitals it sends. A student's phone is
    recorded without them, whatever the body says. A staff login is accepted and
    recorded nowhere.
    """
    if ctx.device_id is not None:
        vitals = payload if payload is not None else HeartbeatRequest()
        store.clicker_seen(ctx.device_id, vitals.rssi, vitals.battery_pct)
    elif ctx.role == "student":
        store.phone_seen(ctx.user_id)
