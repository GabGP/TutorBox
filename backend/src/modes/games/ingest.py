"""Stores a batch of game events, one status per event.

A phone resends what it could not confirm, so an id already stored is a
"duplicate", not an error. A malformed event is "rejected" alone: it must never
block the rest of the phone's queue.
"""

import sqlite3

from pydantic import ValidationError

from core.db.game_event_repository import GameEventRecord, insert_game_event
from modes.games.events import GameEvent
from modes.games.labels import labels_for

__all__ = ["ACCEPTED", "DUPLICATE", "REJECTED", "ingest_events"]

ACCEPTED = "accepted"
DUPLICATE = "duplicate"
REJECTED = "rejected"


def ingest_events(
    conn: sqlite3.Connection,
    install_id: str,
    student_id: int | None,
    raw_events: list[object],
) -> list[str]:
    """One status per raw event, in the order received. The caller commits."""
    return [
        _ingest_one_event(conn, install_id, student_id, raw_event)
        for raw_event in raw_events
    ]


def _ingest_one_event(
    conn: sqlite3.Connection,
    install_id: str,
    student_id: int | None,
    raw_event: object,
) -> str:
    try:
        event = GameEvent.model_validate(raw_event)
    except ValidationError:
        return REJECTED
    labels = labels_for(event.grade, event.lesson_id)
    record = GameEventRecord(
        client_event_id=event.client_event_id,
        install_id=install_id,
        grade=event.grade,
        lesson_id=event.lesson_id,
        round_index=event.round_index,
        attempt=event.attempt,
        is_correct=event.is_correct,
        occurred_at=_sqlite_timestamp(event),
        student_id=student_id,
        answer=event.answer,
        expected=event.expected,
        app_version=event.app_version,
        cnb_topic=labels.cnb_topic,
        concept_topic=labels.concept_topic,
        concept_subconcept=labels.concept_subconcept,
        # A right answer has no mistake behind it, whatever the app sent.
        misconception=None if event.is_correct else event.misconception,
    )
    return ACCEPTED if insert_game_event(conn, record) else DUPLICATE


def _sqlite_timestamp(event: GameEvent) -> str:
    """The event's UTC time as SQLite writes its own: "YYYY-MM-DD HH:MM:SS".

    isoformat, not strftime: on Linux strftime("%Y") does not zero-pad a year
    below 1000, and a phone with a broken clock can report one.
    """
    naive_utc = event.occurred_at.replace(tzinfo=None)
    return naive_utc.isoformat(sep=" ", timespec="seconds")
