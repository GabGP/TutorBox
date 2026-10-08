"""One tutor turn: plan the move, let the model voice it, keep only safe text.

The planner decides the mathematics; the model (when allowed) only rewords or
explains; guard.py decides whether that wording may be shown. When the model is
busy, unreachable or fails the guard, the child gets the deterministic text and
the turn records that containment was triggered.
"""

import logging
from dataclasses import dataclass
from fractions import Fraction

from modes.socratic.gateway import TutorGateway
from modes.socratic.guard import check, clean
from modes.socratic.planner import Move, plan
from modes.socratic.problems import Problem
from modes.socratic.prompts import explain_prompt, rewrite_prompt
from modes.socratic.state import ConversationStore

__all__ = ["SocraticTutor", "TurnResult"]

logger = logging.getLogger(__name__)

EXPLAIN_FOLLOW_UP = "¿Me das un ejemplo tuyo?"


@dataclass(frozen=True)
class TurnResult:
    reply: str
    kind: str
    hint_level: int
    used_model: bool
    containment_triggered: bool
    llm_raw: str | None
    problem: Problem | None
    is_correct: bool | None
    topic_id: str | None
    attempt: Fraction | None = None


class SocraticTutor:
    """Mode 2 tutor: deterministic pedagogy, optional model voice, hard guards."""

    def __init__(self, gateway: TutorGateway, store: ConversationStore) -> None:
        self._gateway = gateway
        self._store = store

    def respond(self, key: str, message: str) -> TurnResult:
        move, conversation = plan(self._store.get(key), message)
        self._store.put(key, conversation)
        reply, raw, used_model, contained = self._voice(move, conversation.problem)
        return TurnResult(
            reply=reply,
            kind=move.kind,
            hint_level=move.level,
            used_model=used_model,
            containment_triggered=contained,
            llm_raw=raw,
            problem=move.problem,
            is_correct=move.is_correct,
            topic_id=move.topic.id if move.topic else None,
            attempt=move.attempt,
        )

    def reset(self, key: str) -> None:
        """Forgets the problem in progress (the chat's 'Empezar de nuevo')."""
        self._store.drop(key)

    def _voice(
        self, move: Move, active: Problem | None
    ) -> tuple[str, str | None, bool, bool]:
        """(reply, raw model text, model reply used, containment triggered).

        `active` is the problem still in progress after this move: an explanation
        given mid-problem must not leak its answer either.
        """
        if move.llm == "none":
            return move.text, None, False, False
        if move.llm == "explain" and move.topic is not None:
            prompt = explain_prompt(move.question, move.topic.title)
        else:
            prompt = rewrite_prompt(move.text)
        raw = self._gateway.complete(prompt)
        if raw is None:
            return move.text, None, False, False
        text = clean(raw)
        issues = check(text, mode=move.llm, source=move.text, problem=active)
        if issues:
            logger.info("Tutor containment (%s): %r", ", ".join(issues), text[:120])
            return move.text, raw, False, True
        if move.llm == "explain" and not text.endswith("?"):
            text = f"{text} {EXPLAIN_FOLLOW_UP}"  # keep it a conversation
        return text, raw, True, False
