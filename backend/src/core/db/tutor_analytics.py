"""Mode 2 analytics, read side: what students practised with the tutor over a period.

Built from turn_logs, which keeps every turn after the login expires. The report
names topics and counts, never what a child wrote or what the tutor answered.
"""

import sqlite3
from dataclasses import dataclass
from datetime import date

from core.db.periods import Period, period_params

__all__ = [
    "MAX_SESSION_SUMMARIES",
    "TutorAnalytics",
    "TutorSessionSummary",
    "TutorTopicActivity",
    "summarize_tutor_analytics",
]

# Newest first; a month of a 30-student class stays well under this.
MAX_SESSION_SUMMARIES = 200

_FROM = (
    "FROM turn_logs t JOIN sessions s ON s.id = t.session_id "
    "JOIN users u ON u.id = s.user_id "
    "WHERE u.role = 'student' AND t.timestamp >= :start AND t.timestamp < :end "
)
# A problem is its text within one login; solved = answered right, stuck = reached
# the last hint (3, the worked analogy).
_PROBLEM = "t.session_id || '|' || COALESCE(t.sympy_evaluated_expression, '')"
_COUNTS = (
    f"COUNT(DISTINCT CASE WHEN t.sympy_is_correct = 1 THEN {_PROBLEM} END), "
    f"COUNT(DISTINCT CASE WHEN t.hint_level >= 3 THEN {_PROBLEM} END)"
)


@dataclass(frozen=True)
class TutorTopicActivity:
    """One topic: how much students asked about it, solved, and got stuck."""

    topic: str
    turns: int
    students: int
    solved: int
    stuck: int


@dataclass(frozen=True)
class TutorSessionSummary:
    """One student's login with the tutor: the topics, not the conversation."""

    student: str
    started_at: str
    last_turn_at: str
    turns: int
    topics: list[str]
    solved: int
    stuck: int


@dataclass(frozen=True)
class TutorAnalytics:
    """The class's tutor use over one period, most asked topic first."""

    period: Period
    start: date
    end: date
    students: int
    sessions: int
    turns: int
    most_asked_topic: str | None
    most_stuck_topic: str | None
    topics: list[TutorTopicActivity]
    session_summaries: list[TutorSessionSummary]


def summarize_tutor_analytics(
    conn: sqlite3.Connection, period: Period, day: date
) -> TutorAnalytics:
    """Topic activity and one summary per login, for the period that holds day."""
    params = {**period_params(period, day), "limit": MAX_SESSION_SUMMARIES}
    students, sessions, turns = conn.execute(
        f"SELECT COUNT(DISTINCT s.user_id), COUNT(DISTINCT t.session_id), COUNT(*) {_FROM}",
        params,
    ).fetchone()
    topics = [
        TutorTopicActivity(*row)
        for row in conn.execute(
            f"SELECT t.concept_topic, COUNT(*) AS n, COUNT(DISTINCT s.user_id), {_COUNTS} "
            f"{_FROM} AND t.concept_topic IS NOT NULL GROUP BY 1 ORDER BY n DESC, 1",
            params,
        )
    ]
    summaries = [
        TutorSessionSummary(
            student,
            first,
            last,
            n,
            sorted(filter(None, (names or "").split(","))),
            ok,
            stuck,
        )
        for student, first, last, n, names, ok, stuck in conn.execute(
            "SELECT u.username, MIN(t.timestamp), MAX(t.timestamp) AS last, COUNT(*), "
            f"GROUP_CONCAT(DISTINCT t.concept_topic), {_COUNTS} {_FROM}"
            "GROUP BY t.session_id ORDER BY last DESC LIMIT :limit",
            params,
        )
    ]
    stuck = [t for t in topics if t.stuck]
    return TutorAnalytics(
        period=period,
        start=date.fromisoformat(params["start"]),
        end=date.fromisoformat(params["end"]),
        students=students,
        sessions=sessions,
        turns=turns,
        most_asked_topic=topics[0].topic if topics else None,
        most_stuck_topic=max(stuck, key=lambda t: t.stuck).topic if stuck else None,
        topics=topics,
        session_summaries=summaries,
    )
