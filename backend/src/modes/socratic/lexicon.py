"""Word lists shared by the planner and the output guard (see lexicon.json)."""

import json
from pathlib import Path

__all__ = ["ENGLISH", "FILLER", "HELP", "QUESTION", "ROLE_WORDS", "RUDE"]

_DATA = json.loads(Path(__file__).with_name("lexicon.json").read_text("utf-8"))

ENGLISH = frozenset(_DATA["english"])
RUDE = frozenset(_DATA["rude"])
ROLE_WORDS = tuple(_DATA["role_words"])
HELP = tuple(_DATA["help"])
FILLER = frozenset(_DATA["filler"])
QUESTION = tuple(_DATA["question"])
