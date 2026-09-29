"""Who is using the tutor, for the teacher's tutor-mode panel.

Kept in memory like the quiz's live state (single worker). A student counts as
connected while the chat is open: it pings every 20 s and every message also
counts. Students drop off the list after 30 minutes without activity.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, replace

__all__ = ["StudentActivity", "TutorRoster"]

ONLINE_SECONDS = 45.0
FORGET_SECONDS = 1800.0


@dataclass(frozen=True)
class StudentActivity:
    username: str
    last_seen: float
    turns: int = 0
    solved: int = 0
    problem: str | None = None
    hint_level: int = 0


class TutorRoster:
    def __init__(
        self,
        online_seconds: float = ONLINE_SECONDS,
        forget_seconds: float = FORGET_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._online = online_seconds
        self._forget = forget_seconds
        self._clock = clock
        self._students: dict[int, StudentActivity] = {}
        self._lock = threading.Lock()

    def seen(self, user_id: int, username: str) -> None:
        """The chat is open on this student's phone."""
        self._update(user_id, username, lambda current: current)

    def record(
        self, user_id: int, username: str, problem: str | None, level: int, solved: bool
    ) -> None:
        """One more message; `problem` is None when the turn was not about one."""

        def apply(current: StudentActivity) -> StudentActivity:
            if solved:
                working_on, hint_level = None, 0
            elif problem:
                working_on, hint_level = problem, level
            else:  # a greeting or a question: the open problem stays open
                working_on, hint_level = current.problem, current.hint_level
            return replace(
                current,
                turns=current.turns + 1,
                solved=current.solved + int(solved),
                problem=working_on,
                hint_level=hint_level,
            )

        self._update(user_id, username, apply)

    def cleared(self, user_id: int, username: str) -> None:
        """The student pressed 'Empezar de nuevo'."""
        self._update(
            user_id, username, lambda c: replace(c, problem=None, hint_level=0)
        )

    def snapshot(self) -> list[dict[str, object]]:
        """Students seen in the last 30 minutes, connected ones first."""
        now = self._clock()
        with self._lock:
            for user_id in [
                uid
                for uid, s in self._students.items()
                if now - s.last_seen > self._forget
            ]:
                del self._students[user_id]
            students = list(self._students.values())
        rows = [
            {
                "username": s.username,
                "online": now - s.last_seen <= self._online,
                "seconds_ago": int(now - s.last_seen),
                "turns": s.turns,
                "solved": s.solved,
                "problem": s.problem,
                "hint_level": s.hint_level,
            }
            for s in students
        ]
        return sorted(rows, key=lambda row: (not row["online"], row["username"]))

    def _update(
        self,
        user_id: int,
        username: str,
        change: Callable[[StudentActivity], StudentActivity],
    ) -> None:
        now = self._clock()
        with self._lock:
            current = self._students.get(user_id) or StudentActivity(username, now)
            updated = change(current)
            self._students[user_id] = replace(updated, username=username, last_seen=now)
