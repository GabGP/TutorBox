"""Pydantic schemas for the clicker authentication endpoint."""

from pydantic import BaseModel, Field

from core.security import DeviceIdField

# A clicker secret is exactly 32 lowercase hex characters; anything else is refused.
DEVICE_SECRET_PATTERN = r"^[0-9a-f]{32}$"


class DeviceAuthRequest(BaseModel):
    device_id: DeviceIdField
    secret: str = Field(..., pattern=DEVICE_SECRET_PATTERN)


class DeviceAuthResponse(BaseModel):
    session_id: str  # the bearer token; the database keeps only its digest
    username: str
    device_id: str
