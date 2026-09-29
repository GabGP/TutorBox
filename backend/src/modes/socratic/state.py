"""Per-login conversation state: the problem being worked on and its hint level.

State lives in memory, keyed by the login session, like the quiz's live state.
The backend runs a single worker (infra/systemd), so one store serves every
phone; the least recently used conversations are dropped past `max_entries`.
"""

import threading
from collections import OrderedDict
from dataclasses import dataclass
from fractions import Fraction

from modes.socratic.problems import Problem

__all__ = ["Conversation", "ConversationStore"]


@dataclass(frozen=True)
class Conversation:
    """What the tutor remembers between two messages of the same child."""

    problem: Problem | None = None
    level: int = 0
    word_numbers: tuple[Fraction, ...] = ()
    topic_id: str | None = None  # just explained: the child may answer with an idea


class ConversationStore:
    """Thread-safe, size-bounded map from login session to Conversation."""

    def __init__(self, max_entries: int = 500) -> None:
        self._items: OrderedDict[str, Conversation] = OrderedDict()
        self._lock = threading.Lock()
        self._max_entries = max_entries

    def get(self, key: str) -> Conversation:
        with self._lock:
            conversation = self._items.get(key, Conversation())
            if key in self._items:
                self._items.move_to_end(key)
            return conversation

    def put(self, key: str, conversation: Conversation) -> None:
        with self._lock:
            self._items[key] = conversation
            self._items.move_to_end(key)
            while len(self._items) > self._max_entries:
                self._items.popitem(last=False)

    def drop(self, key: str) -> None:
        with self._lock:
            self._items.pop(key, None)

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)
