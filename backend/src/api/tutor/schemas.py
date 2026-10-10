"""Pydantic schemas for the Mode 2 tutor chat."""

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "TutorMessageRequest",
    "TutorReplyResponse",
    "TutorRosterResponse",
    "TutorStatusResponse",
    "TutorStudent",
    "TutorSummaryResponse",
]


class TutorMessageRequest(BaseModel):
    """What the child typed. Plain text only: there is no field for files."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The child's message; the tutor itself answers above 280 chars.",
    )


class TutorReplyResponse(BaseModel):
    """The tutor's plain-text Spanish reply."""

    reply: str
    kind: str = Field(
        description="hint, praise, explain, think, word_problem, social, input, "
        "beyond, negative, off_topic, orphan or show_work."
    )
    hint_level: int = Field(ge=0, le=3)
    used_model: bool = Field(
        description="True when the reply is the model's wording that passed the guard."
    )
    topic: str | None = Field(default=None, description="CNB topic id, if any.")


class TutorStatusResponse(BaseModel):
    status: str = "ok"


class TutorStudent(BaseModel):
    """One student in the teacher's tutor panel."""

    username: str
    online: bool = Field(description="Chat open in the last 45 seconds.")
    seconds_ago: int
    turns: int
    solved: int
    problem: str | None = Field(description="Problem in progress, if any.")
    hint_level: int = Field(ge=0, le=3)


class TutorSummaryResponse(BaseModel):
    """Class totals for the wall screen (/pantalla/): public, so no names."""

    online: int = Field(description="Students with the chat open.")
    solved: int = Field(description="Problems solved in the last 30 minutes.")
    need_help: int = Field(description="Connected students on the last hint (3 of 3).")


class TutorRosterResponse(BaseModel):
    students: list[TutorStudent]
