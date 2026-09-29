"""Reading a child's message: a question, a bare answer, or a question on a number."""

import re
from fractions import Fraction

from modes.socratic.curriculum import Topic, load_curriculum
from modes.socratic.lexicon import FILLER, QUESTION
from modes.socratic.numbers import extract_numbers
from modes.socratic.text import Folded

__all__ = ["bare_answer", "is_question", "numeric_topic"]

_DIGITS = re.compile(r"[\d.,/%]+")


def is_question(folded: Folded) -> bool:
    """'cuántos...', 'cómo...', or a message starting with 'qué'.

    'que es' elsewhere is not a question: 'creo que es 68' is an answer.
    """
    return folded.has_any(QUESTION) or folded.tokens[:1] == ("que",)


def bare_answer(message: str, folded: Folded) -> Fraction | None:
    """'68', 'es 68', 'creo que es 3/4': one number and no question."""
    numbers = extract_numbers(message)
    if len(numbers) != 1 or is_question(folded):
        return None
    words = Folded.of(_DIGITS.sub(" ", message)).tokens
    other = [word for word in words if word not in FILLER]
    return numbers[0] if len(other) <= 1 else None


def numeric_topic(message: str, folded: Folded) -> Topic | None:
    """A question about a written number with no topic word ('¿qué es 3/4?')."""
    if not (extract_numbers(message) and is_question(folded)):
        return None
    topic_id = "fracciones" if "/" in message else "numeracion"
    return load_curriculum().get(topic_id)
