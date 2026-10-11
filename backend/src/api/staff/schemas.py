"""Pydantic schemas for staff management endpoints."""

from typing import Any

from pydantic import BaseModel

from core.security import DeviceIdField, PinField, RoleField, UsernameField


class CreateUserRequest(BaseModel):
    username: UsernameField
    pin: PinField
    role: RoleField = "student"


class CreateUserResponse(BaseModel):
    username: str
    role: str


class UserListResponse(BaseModel):
    users: list[dict[str, Any]]


class ResetPinResponse(BaseModel):
    username: str
    temporary_pin: str


class DeleteUserResponse(BaseModel):
    detail: str = "Account deleted."


class RecoverUserRequest(BaseModel):
    username: UsernameField


class RecoverUserResponse(BaseModel):
    username: str
    temporary_pin: str
    detail: str = "Account recovered. User must set a new PIN on next login."


class DeviceItem(BaseModel):
    device_id: str
    assigned_user_id: int | None = None
    assigned_username: str | None = None
    created_at: str
    # Fleet health, filled once the clicker checks in (api/clicker): enrolled means
    # it holds a secret; online means it checked in within the last 45 seconds.
    enrolled: bool = False
    online: bool = False
    last_seen_at: str | None = None
    rssi: int | None = None
    battery_mv: int | None = None
    firmware: str | None = None


class DeviceListResponse(BaseModel):
    devices: list[DeviceItem]


class RegisterDeviceRequest(BaseModel):
    device_id: DeviceIdField


class DeviceMessageResponse(BaseModel):
    detail: str


class AssignDeviceRequest(BaseModel):
    user_id: int


class AssignDeviceResponse(BaseModel):
    device_id: str
    assigned_user_id: int
    assigned_username: str


class AuditLogsResponse(BaseModel):
    logs: list[dict[str, Any]]
