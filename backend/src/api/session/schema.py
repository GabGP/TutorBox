"""Pydantic schemas for the Quiz Session REST API endpoints."""

from pydantic import BaseModel, Field

from session.models import RoundTally, TurnDecision


class CreateSessionRequest(BaseModel):
    """Payload for provisioning a new quiz match in lobby state."""

    title: str = Field(..., min_length=1, max_length=120)
    topic: str = Field(..., min_length=1, max_length=64)
    question_ids: list[str] = Field(..., min_length=1)
    duration_seconds: int = Field(default=30, ge=5, le=300)


class CastVoteRequest(BaseModel):
    """Payload for an individual student vote submission."""

    selected_option: str = Field(..., pattern=r"^[A-D]$")
    transport_type: str = "web"
    device_id: str | None = None
    response_time_ms: float | None = Field(default=None, ge=0.0)


class SessionRoundInfo(BaseModel):
    """Summary of current question round state and countdown."""

    round_id: str
    round_index: int
    status: str
    question_id: str | None = None
    duration_seconds: int = 30
    time_remaining: float | None = None


class SessionStateResponse(BaseModel):
    """Publicly inspectable state of a quiz session and active round."""

    id: str
    title: str
    topic: str
    status: str
    current_round_index: int
    question_count: int
    current_round: SessionRoundInfo | None = None


class RoundRevealResponse(BaseModel):
    """Turn resolution outcome with distributions and pedagogical remediation decision."""

    round_id: str
    status: str = "revealed"
    tally: RoundTally
    decision: TurnDecision


class VoteResponse(BaseModel):
    """Acknowledgment payload returned upon successful vote persistence."""

    vote_id: str
    session_id: str
    round_id: str
    student_id: int
    selected_option: str
    recorded_at: str | None = None


class SessionReportResponse(BaseModel):
    """Longitudinal summary report of a completed or active quiz match."""

    session_id: str
    title: str
    topic: str
    status: str
    total_rounds: int
    total_votes_cast: int
    average_accuracy_percentage: float
