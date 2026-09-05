"""Domain models and value objects for quiz sessions, rounds, and votes."""

from enum import Enum

from pydantic import BaseModel, Field

VALID_OPTIONS: tuple[str, ...] = ("A", "B", "C", "D")


class SessionStatus(str, Enum):
    LOBBY = "lobby"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class RoundStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    REVEALED = "revealed"


class TransportType(str, Enum):
    WEB = "web"
    HARDWARE = "hardware"
    MOCK = "mock"


class QuizSessionRecord(BaseModel):
    """Represents a quiz match session stored in the database."""

    id: str
    title: str
    topic: str
    teacher_id: int | None = None
    status: str = SessionStatus.LOBBY.value
    question_count: int = 0
    current_round_index: int = 0
    created_at: str | None = None
    started_at: str | None = None
    ended_at: str | None = None


class QuizRoundRecord(BaseModel):
    """Represents an individual question round within a session."""

    id: str
    session_id: str
    question_id: str | None = None
    round_index: int
    status: str = RoundStatus.PENDING.value
    opened_at: str | None = None
    closed_at: str | None = None
    duration_seconds: int = 30


class StudentVoteRecord(BaseModel):
    """Represents an individual student's immutable vote submission."""

    id: str
    session_id: str
    round_id: str
    student_id: int
    transport_type: str = TransportType.WEB.value
    device_id: str | None = None
    selected_option: str
    is_correct: bool = False
    misconception: str | None = None
    response_time_ms: float | None = None
    created_at: str | None = None


class RoundTally(BaseModel):
    """Aggregated vote distribution and participation summary for a round."""

    counts: dict[str, int] = Field(
        default_factory=lambda: {"A": 0, "B": 0, "C": 0, "D": 0}
    )
    total_votes: int = 0
    percentages: dict[str, float] = Field(
        default_factory=lambda: {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0}
    )
    correct_option: str
    correct_count: int = 0
    correct_percentage: float = 0.0


class TurnDecision(BaseModel):
    """Pedagogical decision outcome evaluated after voting closes."""

    should_speak: bool = False
    reason: str
    dominant_distractor: str | None = None
    dominant_percentage: float = 0.0
    misconception: str | None = None
    explanation: str | None = None


class SessionSummary(BaseModel):
    """High-level summary of a quiz match upon conclusion."""

    session_id: str
    title: str
    topic: str
    status: str
    total_rounds: int
    total_votes_cast: int
    average_accuracy_percentage: float
