import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from db.audit import record_audit
from db.database import get_db
from security import (
    AuthContext,
    DeviceIdField,
    require_roles,
)

logger = logging.getLogger(__name__)
DEFAULT_DEVICE_LIST_LIMIT: int = 1000
router = APIRouter()


class DeviceItem(BaseModel):
    device_id: str
    assigned_user_id: int | None = None
    assigned_username: str | None = None
    created_at: str


class DeviceListResponse(BaseModel):
    devices: list[DeviceItem]


class RegisterDeviceRequest(BaseModel):
    device_id: DeviceIdField


class DeviceMessageResponse(BaseModel):
    detail: str


@router.get("/devices", response_model=DeviceListResponse)
def list_devices(
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    """Lists all registered physical clickers with linked student roster info."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT d.device_id, d.assigned_user_id, d.created_at, u.username AS assigned_username "
            "FROM devices d LEFT JOIN users u ON d.assigned_user_id = u.id "
            "ORDER BY d.device_id LIMIT ?",
            (DEFAULT_DEVICE_LIST_LIMIT,),
        )
        rows = cursor.fetchall()

    return DeviceListResponse(
        devices=[
            DeviceItem(
                device_id=r["device_id"],
                assigned_user_id=r["assigned_user_id"],
                assigned_username=r["assigned_username"],
                created_at=r["created_at"],
            )
            for r in rows
        ]
    )


@router.post(
    "/devices",
    response_model=DeviceItem,
    status_code=status.HTTP_201_CREATED,
)
def register_device(
    payload: RegisterDeviceRequest,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    """Registers a new physical clicker identifier into the fleet."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO devices (device_id) VALUES (?)",
                (payload.device_id,),
            )
            record_audit(conn, actor_user_id=ctx.user_id, action="device_registered")
            conn.commit()
            cursor.execute(
                "SELECT device_id, assigned_user_id, created_at FROM devices WHERE device_id = ?",
                (payload.device_id,),
            )
            row = cursor.fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device ID already registered.",
        )

    return DeviceItem(
        device_id=row["device_id"],
        assigned_user_id=row["assigned_user_id"],
        assigned_username=None,
        created_at=row["created_at"],
    )


@router.delete("/devices/{device_id}", response_model=DeviceMessageResponse)
def delete_device(
    device_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
):
    """Removes a physical clicker from the appliance fleet."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT device_id FROM devices WHERE device_id = ?", (device_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found."
            )

        cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
        record_audit(conn, actor_user_id=ctx.user_id, action="device_deleted")
        conn.commit()

    return DeviceMessageResponse(detail="Device removed from fleet.")
