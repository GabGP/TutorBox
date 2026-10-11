"""Pydantic schemas for the presence heartbeat and the teacher's class view."""

from typing import Annotated

from pydantic import BaseModel, Field

from api.presence.status import ConnectionStatus, SignalLevel

__all__ = [
    "ClassPresenceResponse",
    "ClickerPresence",
    "HeartbeatRequest",
    "PhonePresence",
    "StudentPresence",
]

RssiDbm = Annotated[int, Field(ge=-120, le=0)]
BatteryPercent = Annotated[int, Field(ge=0, le=100)]


class HeartbeatRequest(BaseModel):
    """What a clicker reports with its heartbeat. Phones send no body at all."""

    rssi: RssiDbm | None = Field(
        default=None, description="Wi-Fi signal of the clicker in dBm, -120 to 0."
    )
    battery_pct: BatteryPercent | None = Field(
        default=None, description="Battery of the clicker in percent, 0 to 100."
    )


class PhonePresence(BaseModel):
    """The student's phone."""

    status: ConnectionStatus
    seconds_ago: int | None = Field(description="None when absent.")


class ClickerPresence(BaseModel):
    """The clicker assigned to the student, with its last reported vitals."""

    device_id: str
    status: ConnectionStatus
    seconds_ago: int | None = Field(description="None when absent.")
    signal: SignalLevel | None = Field(description="None when no RSSI is known.")
    rssi: int | None
    battery_pct: int | None


class StudentPresence(BaseModel):
    """One student in the class, with the better status of phone and clicker."""

    user_id: int
    username: str
    status: ConnectionStatus
    phone: PhonePresence
    clicker: ClickerPresence | None = Field(description="None without a clicker.")


class ClassPresenceResponse(BaseModel):
    """The whole class as the teacher's lobby lists it."""

    online: int = Field(description="Students whose status is online.")
    total: int = Field(description="Students listed.")
    students: list[StudentPresence]
    unassigned_clickers: list[str] = Field(
        description="Registered clickers that no listed student has."
    )
