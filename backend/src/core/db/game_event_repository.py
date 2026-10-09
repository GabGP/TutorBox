"""Mode 3 telemetry: one game_events row per answer tapped in a grade app (docs/database/games.md)."""

import sqlite3
from dataclasses import dataclass

__all__ = ["GameEventRecord", "insert_game_event"]


@dataclass(frozen=True)
class GameEventRecord:
    """An answer tapped in a game, as stored."""

    client_event_id: str
    install_id: str
    grade: str
    lesson_id: str
    round_index: int
    attempt: int
    is_correct: bool
    occurred_at: str  # UTC, "YYYY-MM-DD HH:MM:SS", the phone's clock
    student_id: int | None = None
    answer: str | None = None
    expected: str | None = None
    app_version: str | None = None
    cnb_topic: str | None = None
    concept_topic: str | None = None
    concept_subconcept: str | None = None
    misconception: str | None = None


def insert_game_event(conn: sqlite3.Connection, record: GameEventRecord) -> bool:
    """Stores the event unless its client_event_id is already stored. The caller commits.

    Returns True when a row was inserted and False when the id was already there.
    """
    cursor = conn.execute(
        "INSERT INTO game_events (client_event_id, install_id, grade, lesson_id, "
        "round_index, attempt, is_correct, occurred_at, student_id, answer, expected, "
        "app_version, cnb_topic, concept_topic, concept_subconcept, misconception) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(client_event_id) DO NOTHING",
        (
            record.client_event_id,
            record.install_id,
            record.grade,
            record.lesson_id,
            record.round_index,
            record.attempt,
            int(record.is_correct),
            record.occurred_at,
            record.student_id,
            record.answer,
            record.expected,
            record.app_version,
            record.cnb_topic,
            record.concept_topic,
            record.concept_subconcept,
            record.misconception,
        ),
    )
    return cursor.rowcount == 1
