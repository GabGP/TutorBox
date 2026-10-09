"""Pydantic schemas for the Quiz Session REST API endpoints."""

from pydantic import BaseModel, Field

from modes.quiz.session.models import RoundTally, TurnDecision


class CreateSessionRequest(BaseModel):
    """Payload for provisioning a new quiz match in lobby state."""

    title: str = Field(..., min_length=1, max_length=120)
    topic: str = Field(..., min_length=1, max_length=64)
    question_ids: list[str] = Field(..., min_length=1)
    duration_seconds: int = Field(default=30, ge=5, le=300)


class CastVoteRequest(BaseModel):
    """A student's vote, from a phone or from an ESP32 clicker.

    The server labels the vote from the caller's session: `hardware` with the
    clicker's id when the token was issued to a clicker, otherwise `web`. The body
    cannot choose the label; other fields a client sends, such as `transport_type`
    or `device_id`, are ignored.
    """

    selected_option: str = Field(..., pattern=r"^[A-D]$")
    response_time_ms: float | None = Field(default=None, ge=0.0)


class RoundRevealResponse(BaseModel):
    """Turn resolution outcome with distributions and pedagogical remediation decision."""

    round_id: str
    status: str = "revealed"
    tally: RoundTally
    decision: TurnDecision


class RoundQuestionView(BaseModel):
    """Answer-free question view safe for student clients and the classroom screen."""

    question_text: str
    options: dict[str, str]


class RoundResultView(RoundRevealResponse):
    """Published once a round is revealed: the answer is on the classroom screen by then."""

    explanations: dict[str, str] = Field(default_factory=dict)


class SessionRoundInfo(BaseModel):
    """Summary of current question round state, countdown, and phase-gated content."""

    round_id: str
    round_index: int
    status: str
    question_id: str | None = None
    duration_seconds: int = 30
    time_remaining: float | None = None
    votes_cast: int = 0
    question: RoundQuestionView | None = None
    result: RoundResultView | None = None


class SessionStateResponse(BaseModel):
    """Publicly inspectable state of a quiz session and active round."""

    id: str
    title: str
    topic: str
    status: str
    current_round_index: int
    question_count: int
    current_round: SessionRoundInfo | None = None


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
