"""Real-time quiz session state machine and turn coordinator."""

import sqlite3
from collections.abc import Callable
from typing import Any

from session.models import (
    QuizRoundRecord,
    QuizSessionRecord,
    RoundTally,
    StudentVoteRecord,
    TurnDecision,
)
from session.session_manager import (
    activate_quiz_session,
    advance_quiz_session,
    initialize_quiz_session,
)
from session.timer import RoundTimer
from session.turn_manager import close_turn_round, open_turn_round, reveal_turn_round
from session.vote_processor import process_student_vote

EventListener = Callable[[str, dict[str, Any]], None]

_SHARED_TIMERS: dict[str, RoundTimer] = {}
_SHARED_LISTENERS: list[EventListener] = []


def reset_shared_session_state() -> None:
    """Resets in-memory timers and listeners for clean test isolation."""
    _SHARED_TIMERS.clear()
    _SHARED_LISTENERS.clear()


class QuizSessionEngine:
    """Coordinates real-time session progression, voting locks, and turn decisions."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        timers: dict[str, RoundTimer] | None = None,
        listeners: list[EventListener] | None = None,
    ) -> None:
        self.conn = conn
        self._timers = timers if timers is not None else _SHARED_TIMERS
        self._listeners = listeners if listeners is not None else _SHARED_LISTENERS

    def add_event_listener(self, listener: EventListener) -> None:
        """Registers an open listener hook for Student B transports or telemetry."""
        self._listeners.append(listener)

    def _emit(self, event_name: str, payload: dict[str, Any]) -> None:
        for listener in self._listeners:
            listener(event_name, payload)

    def get_remaining_time(self, round_id: str) -> float | None:
        """Returns remaining seconds for round timer, or None if unmanaged."""
        timer = self._timers.get(round_id)
        if timer is None:
            return None
        return round(timer.remaining_seconds(), 1) if timer.is_running() else 0.0

    def create_session(
        self,
        session_id: str,
        title: str,
        topic: str,
        question_ids: list[str],
        *,
        teacher_id: int | None = None,
        duration_seconds: int = 30,
    ) -> QuizSessionRecord:
        """Initializes a new quiz match in lobby state and provisions question rounds."""
        return initialize_quiz_session(
            self.conn,
            session_id,
            title,
            topic,
            question_ids,
            teacher_id=teacher_id,
            duration_seconds=duration_seconds,
        )

    def start_session(self, session_id: str) -> QuizRoundRecord:
        """Transitions session from lobby to active and opens the initial round."""
        activate_quiz_session(self.conn, session_id)
        return self.open_round(session_id, 0)

    def open_round(self, session_id: str, round_index: int) -> QuizRoundRecord:
        """Opens a question round for voting and activates its countdown timer."""
        round_rec = open_turn_round(self.conn, self._timers, session_id, round_index)
        self._emit("round_opened", {"round_id": round_rec.id, "index": round_index})
        return round_rec

    def cast_vote(
        self,
        session_id: str,
        round_id: str,
        student_id: int,
        selected_option: str,
        *,
        response_time_ms: float | None = None,
        transport_type: str = "web",
        device_id: str | None = None,
    ) -> StudentVoteRecord:
        """Submits a student vote enforcing the first-press lock constraint."""
        vote = process_student_vote(
            self.conn,
            session_id,
            round_id,
            student_id,
            selected_option,
            timer=self._timers.get(round_id),
            response_time_ms=response_time_ms,
            transport_type=transport_type,
            device_id=device_id,
        )
        self._emit("vote_cast", {"round_id": round_id, "student_id": student_id})
        return vote

    def close_round(self, session_id: str, round_id: str) -> QuizRoundRecord:
        """Closes active voting round and terminates its countdown timer."""
        round_rec = close_turn_round(self.conn, self._timers, round_id)
        self._emit("round_closed", {"round_id": round_id})
        return round_rec

    def reveal_round(
        self, session_id: str, round_id: str
    ) -> tuple[RoundTally, TurnDecision]:
        """Calculates vote tallies and evaluates the deterministic >51% Rule."""
        tally, decision = reveal_turn_round(self.conn, self._timers, round_id)
        event_data = {
            "round_id": round_id,
            "should_speak": decision.should_speak,
            "tally": tally.model_dump(),
        }
        self._emit("round_revealed", event_data)
        return tally, decision

    def next_round(self, session_id: str) -> QuizRoundRecord | None:
        """Advances to the subsequent question round or completes the match."""
        next_index = advance_quiz_session(self.conn, session_id)
        if next_index is not None:
            return self.open_round(session_id, next_index)
        self._emit("session_completed", {"session_id": session_id})
        return None
