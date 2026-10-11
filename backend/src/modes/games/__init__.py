"""Mode 3: Offline Primary Educational Games (Week 6).

The grade apps in pwa/tareas send one event per answer tapped when the phone
reaches the appliance. This package validates each event, names what its lesson
practises and stores it once.
"""

from modes.games.events import CLIENT_ID_PATTERN, MISCONCEPTION_PATTERN, GameEvent
from modes.games.ingest import ACCEPTED, DUPLICATE, REJECTED, ingest_events
from modes.games.labels import GameLabels, labels_for, load_lesson_topics

__all__ = [
    "ACCEPTED",
    "CLIENT_ID_PATTERN",
    "DUPLICATE",
    "MISCONCEPTION_PATTERN",
    "REJECTED",
    "GameEvent",
    "GameLabels",
    "ingest_events",
    "labels_for",
    "load_lesson_topics",
]
