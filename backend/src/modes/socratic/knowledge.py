"""The tutor's pre-written knowledge (knowledge_base.json), verified in CI.

Written offline with a frontier model (docs/tutor/knowledge-base-brief.md) and
looked up by exact key, never searched: explanations by CNB topic id, five
Socratic questions per misconception slug and five wordings of every hint
template. The wording is picked from the problem's text (`seed_of`), so a hint is
a pure function of the problem and the level. test_knowledge_base.py checks
every text with the output guard and every written equality with the math engine.
"""

import json
import zlib
from functools import lru_cache
from pathlib import Path

__all__ = [
    "explanations",
    "load_knowledge",
    "misconception_question",
    "phrase",
    "seed_of",
    "variant",
]

_DATA_FILE = Path(__file__).with_name("knowledge_base.json")


@lru_cache(maxsize=1)
def load_knowledge(path: Path = _DATA_FILE) -> dict[str, dict]:
    """Parses the knowledge base once per process."""
    return json.loads(path.read_text(encoding="utf-8"))


def explanations(topic_id: str) -> tuple[str, ...]:
    """The pre-written explanations of a CNB topic; none for an unknown topic."""
    return tuple(load_knowledge()["explanations"].get(topic_id, ()))


def misconception_question(slug: str, text: str) -> str | None:
    """One of the slug's questions (`text`, the problem, picks it); {p} is the problem."""
    questions = load_knowledge()["misconceptions"].get(slug)
    return questions[seed_of(text) % len(questions)] if questions else None


def variant(key: str, seed: int) -> str:
    """One of the pre-written wordings of a phrase; the same seed, the same one."""
    wordings = load_knowledge()["paraphrases"][key]
    return wordings[seed % len(wordings)]


def seed_of(text: str) -> int:
    """A seed that is the same in every process (Python's hash() is not)."""
    return zlib.crc32(text.encode())


def phrase(key: str, text: str, /, **values: object) -> str:
    """The wording of a hint template that `text` (the problem) picks, filled in."""
    return variant(key, seed_of(text)).format(**values)
