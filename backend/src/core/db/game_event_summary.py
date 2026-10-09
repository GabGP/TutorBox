"""Mode 3 telemetry, read side: counts of the game_events rows stored (docs/database/games.md)."""

import sqlite3
from dataclasses import dataclass

__all__ = [
    "MAX_LESSONS_IN_SUMMARY",
    "GameEventSummary",
    "LessonEventCount",
    "summarize_game_events",
]

# A lesson id is whatever a phone sent, so the number of groups has no natural bound.
MAX_LESSONS_IN_SUMMARY = 200

_INSTALL_FILTER = "(:install_id IS NULL OR install_id = :install_id)"


@dataclass(frozen=True)
class LessonEventCount:
    """The answers stored for one lesson of one grade app."""

    grade: str
    lesson_id: str
    cnb_topic: str | None
    concept_topic: str | None
    concept_subconcept: str | None
    events: int
    wrong_events: int


@dataclass(frozen=True)
class GameEventSummary:
    """The answers stored, in total and per lesson."""

    events: int
    wrong_events: int
    installs: int
    lessons: list[LessonEventCount]


def summarize_game_events(
    conn: sqlite3.Connection, install_id: str | None = None
) -> GameEventSummary:
    """Counts the stored answers, of every phone or of the one with that install id.

    Lessons come with the most wrong answers first, at most MAX_LESSONS_IN_SUMMARY.
    """
    parameters = {"install_id": install_id, "limit": MAX_LESSONS_IN_SUMMARY}
    totals = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(is_correct = 0), 0), COUNT(DISTINCT install_id) "
        f"FROM game_events WHERE {_INSTALL_FILTER}",
        parameters,
    ).fetchone()
    lesson_rows = conn.execute(
        "SELECT grade, lesson_id, MAX(cnb_topic), MAX(concept_topic), "
        "MAX(concept_subconcept), COUNT(*) AS events, SUM(is_correct = 0) AS wrong_events "
        f"FROM game_events WHERE {_INSTALL_FILTER} "
        "GROUP BY grade, lesson_id "
        "ORDER BY wrong_events DESC, events DESC, grade, lesson_id LIMIT :limit",
        parameters,
    ).fetchall()
    return GameEventSummary(
        events=totals[0],
        wrong_events=totals[1],
        installs=totals[2],
        lessons=[LessonEventCount(*row) for row in lesson_rows],
    )
