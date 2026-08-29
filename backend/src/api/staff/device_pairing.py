import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db.audit import record_audit
from db.database import get_db
from security import (
    AuthContext,
    require_roles,
)

from .devices import DeviceMessageResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class AssignDeviceRequest(BaseModel):
    user_id: int


class AssignDeviceResponse(BaseModel):
    device_id: str
    assigned_user_id: int
    assigned_username: str


@router.post("/devices/{device_id}/assign", response_model=AssignDeviceResponse)
def assign_device(
    device_id: str,
    payload: AssignDeviceRequest,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    """Links a physical clicker to a student user account."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT device_id FROM devices WHERE device_id = ?", (device_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found."
            )

        cursor.execute(
            "SELECT id, username, role, deleted_at FROM users WHERE id = ?",
            (payload.user_id,),
        )
        user_row = cursor.fetchone()
        if not user_row or user_row["deleted_at"] is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student user not found.",
            )
        if user_row["role"] != "student":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Only student accounts may be assigned to clickers.",
            )

        # Clear existing assignment if this student already held another device
        cursor.execute(
            "UPDATE devices SET assigned_user_id = NULL WHERE assigned_user_id = ?",
            (payload.user_id,),
        )
        # Assign student to this device
        cursor.execute(
            "UPDATE devices SET assigned_user_id = ? WHERE device_id = ?",
            (payload.user_id, device_id),
        )
        record_audit(
            conn,
            actor_user_id=ctx.user_id,
            action="device_assigned",
            target_user_id=payload.user_id,
        )
        conn.commit()

    return AssignDeviceResponse(
        device_id=device_id,
        assigned_user_id=payload.user_id,
        assigned_username=user_row["username"],
    )


@router.post("/devices/{device_id}/unassign", response_model=DeviceMessageResponse)
def unassign_device(
    device_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    """Unlinks a physical clicker from any student."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT device_id, assigned_user_id FROM devices WHERE device_id = ?",
            (device_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found."
            )

        prev_user_id = row["assigned_user_id"]
        cursor.execute(
            "UPDATE devices SET assigned_user_id = NULL WHERE device_id = ?",
            (device_id,),
        )
        if prev_user_id is not None:
            record_audit(
                conn,
                actor_user_id=ctx.user_id,
                action="device_unassigned",
                target_user_id=prev_user_id,
            )
        conn.commit()

    return DeviceMessageResponse(detail="Device unassigned successfully.")
