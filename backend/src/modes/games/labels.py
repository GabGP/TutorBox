"""The concept labels of a lesson played in a grade app (pwa/tareas).

A game names its content by grade and lesson id. This module names it the way the
tutor's turn_logs do: a CNB topic for every lesson, and the quiz's
CURRICULUM_TAXONOMY topic and subconcept where the quiz has that concept. The
taxonomy strings are literals here, not imports; the tests check them against the
quiz taxonomy and against the tutor's labels.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

__all__ = ["GameLabels", "labels_for", "load_lesson_topics"]

_DATA_FILE = Path(__file__).with_name("lesson_topics.json")


@dataclass(frozen=True)
class GameLabels:
    """What a lesson practises; a field is None when the lesson does not name it."""

    cnb_topic: str | None = None  # cnb_matematicas.json topic id
    concept_topic: str | None = None  # CURRICULUM_TAXONOMY topic
    concept_subconcept: str | None = None  # CURRICULUM_TAXONOMY subconcept


# The CNB topics of the games that the quiz taxonomy also has.
_TAXONOMY_BY_CNB_TOPIC: dict[str, tuple[str, str | None]] = {
    "suma_resta": ("arithmetic", "addition_subtraction"),
    "multiplicacion": ("arithmetic", "multiplication_division"),
    "division": ("arithmetic", "multiplication_division"),
    "fracciones": ("fractions", None),
}


@lru_cache(maxsize=1)
def load_lesson_topics() -> dict[str, dict[str, str]]:
    """Parses the lesson table once per process: grade -> lesson id -> CNB topic id."""
    return json.loads(_DATA_FILE.read_text(encoding="utf-8"))


def labels_for(grade: str, lesson_id: str) -> GameLabels:
    """The labels of a game lesson; an unknown grade or lesson has none."""
    cnb_topic = load_lesson_topics().get(grade, {}).get(lesson_id)
    if cnb_topic is None:
        # A game newer than the table is logged without labels, never refused.
        return GameLabels()
    topic, subconcept = _TAXONOMY_BY_CNB_TOPIC.get(cnb_topic, (None, None))
    return GameLabels(cnb_topic, topic, subconcept)
