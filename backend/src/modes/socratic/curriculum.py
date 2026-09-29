"""CNB mathematics topics (1.º to 5.º primaria) the tutor is allowed to teach.

The topic list lives in cnb_matematicas.json, built from the curriculum documents
in pwa/tareas/cnb. A message is in scope when it names one of those topics;
anything from later grades (derivadas, raíz cuadrada, negativos...) is refused.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from modes.socratic.text import Folded

__all__ = ["Curriculum", "Topic", "load_curriculum"]

_DATA_FILE = Path(__file__).with_name("cnb_matematicas.json")


@dataclass(frozen=True)
class Topic:
    id: str
    title: str
    grades: tuple[int, ...]
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class Curriculum:
    topics: tuple[Topic, ...]
    beyond: tuple[str, ...]

    def match(self, message: Folded) -> Topic | None:
        """The first CNB topic the message names, if any."""
        return next((t for t in self.topics if message.has_any(t.keywords)), None)

    def is_beyond(self, message: Folded) -> bool:
        """True for mathematics that belongs to later grades than 5.º primaria."""
        return message.has_any(self.beyond)

    def mentions_math(self, message: Folded) -> bool:
        return self.match(message) is not None

    def get(self, topic_id: str) -> Topic | None:
        return next((t for t in self.topics if t.id == topic_id), None)


@lru_cache(maxsize=1)
def load_curriculum(path: Path = _DATA_FILE) -> Curriculum:
    """Parses the CNB topic file once per process."""
    data = json.loads(path.read_text(encoding="utf-8"))
    topics = tuple(
        Topic(
            id=entry["id"],
            title=entry["title"],
            grades=tuple(entry["grades"]),
            keywords=tuple(entry["keywords"]),
        )
        for entry in data["topics"]
    )
    return Curriculum(topics=topics, beyond=tuple(data["beyond_curriculum"]))
