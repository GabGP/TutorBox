"""The tutor's pre-written knowledge (knowledge_base.json), verified in CI.

Written offline with a frontier model (docs/tutor/knowledge-base-brief.md) and
looked up by exact key, never searched: explanations by CNB topic id, and one
Socratic question per misconception slug. test_knowledge_base.py checks every
text with the output guard and every written equality with the math engine.
"""

import json
from functools import lru_cache
from pathlib import Path

__all__ = ["explanations", "load_knowledge", "misconception_question"]

_DATA_FILE = Path(__file__).with_name("knowledge_base.json")


@lru_cache(maxsize=1)
def load_knowledge(path: Path = _DATA_FILE) -> dict[str, dict]:
    """Parses the knowledge base once per process."""
    return json.loads(path.read_text(encoding="utf-8"))


def explanations(topic_id: str) -> tuple[str, ...]:
    """The pre-written explanations of a CNB topic; none for an unknown topic."""
    return tuple(load_knowledge()["explanations"].get(topic_id, ()))


def misconception_question(slug: str) -> str | None:
    """The question for a misconception, with {p} for the child's problem."""
    return load_knowledge()["misconceptions"].get(slug)
