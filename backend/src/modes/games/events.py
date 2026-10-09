"""One answer tapped in a grade app, as the phone reports it (docs/api/games.md)."""

from datetime import datetime, timezone

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
)

__all__ = ["CLIENT_ID_PATTERN", "GameEvent"]

# Ids are generated on the phone: 16 to 64 URL-safe characters.
CLIENT_ID_PATTERN = r"^[A-Za-z0-9_-]{16,64}$"


class GameEvent(BaseModel):
    """An answer tapped in a game. Unknown fields are ignored so a newer app can still report to an older appliance."""

    model_config = ConfigDict(extra="ignore")

    client_event_id: str = Field(pattern=CLIENT_ID_PATTERN)
    grade: str = Field(pattern=r"^[a-z]{3,16}$")
    lesson_id: str = Field(pattern=r"^[a-z0-9-]{1,64}$")
    round_index: int = Field(ge=0, le=999)
    attempt: int = Field(ge=1, le=99)
    is_correct: StrictBool
    occurred_at: AwareDatetime
    answer: str | None = Field(default=None, max_length=64)
    expected: str | None = Field(default=None, max_length=64)
    app_version: str | None = Field(default=None, max_length=16)

    @field_validator("occurred_at")
    @classmethod
    def _to_utc(cls, value: datetime) -> datetime:
        try:
            return value.astimezone(timezone.utc)
        except OverflowError as error:  # e.g. year 1 with a +14:00 offset
            raise ValueError("occurred_at is out of range") from error
