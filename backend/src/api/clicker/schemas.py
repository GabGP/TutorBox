"""Pydantic schemas for the hardware clicker transport (Week 7).

Kept flat and small on purpose: an ESP32 parses these responses with ArduinoJson.
"""

from pydantic import BaseModel, Field

# Round ids are minted by the session engine: "<session id>_r<index>".
ROUND_ID_PATTERN = r"^[A-Za-z0-9_.-]{1,64}$"


class CheckinRequest(BaseModel):
    """Vitals the clicker reports with each check-in; all optional."""

    firmware: str | None = Field(
        default=None, max_length=32, pattern=r"^[A-Za-z0-9_.+-]+$"
    )
    rssi: int | None = Field(default=None, ge=-127, le=0)
    battery_mv: int | None = Field(default=None, ge=0, le=10_000)


class CheckinResponse(BaseModel):
    """Everything the clicker needs to light its LED: assignment and the open round."""

    device_id: str
    assigned: bool
    round_id: str | None = None
    round_open: bool = False
    voted: bool = False


class ClickerVoteRequest(BaseModel):
    """A button press bound to the round the clicker saw open, never "whatever is
    current", so a press for question 3 cannot land on question 4."""

    round_id: str = Field(..., pattern=ROUND_ID_PATTERN)
    selected_option: str = Field(..., pattern=r"^[A-D]$")
    response_time_ms: float | None = Field(default=None, ge=0.0)


class ClickerVoteResponse(BaseModel):
    vote_id: str
    round_id: str
    selected_option: str
    recorded_at: str | None = None
