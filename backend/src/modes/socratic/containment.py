"""SymPy containment: does a text give the problem's answer away?

Until the child finds it, no text may state an accepted answer outside the
problem itself, in any form: digits (68, 136/2, 7.0), words (sesenta y ocho) or
an expression or assignment that SymPy evaluates to it (x = 12 - 5, «doce menos
cinco», (12 - 4) ÷ 2). Model replies (guard.py) and the deterministic hints
(hints.py) pass this same check, so a blocked reply always falls back to a hint
that passed it.
"""

import re

import sympy as sp

from core.math_engine import are_values_equivalent, safe_parse
from core.math_engine.equation_parser import PARSE_ERRORS
from core.math_engine.safe_parser import MAX_EXPRESSION_LENGTH
from modes.socratic.numbers import digits_for_words, extract_numbers
from modes.socratic.problems import Problem, accepted_answers, normalize

__all__ = ["expressions", "leaks"]

_SENTENCE_END = re.compile(r"\.(?!\d)")  # a decimal point has a digit after it
_SPAN = re.compile(r"[(\d][\d\s+\-×÷*/^().]*[\d)]")
_OPERATOR = re.compile(r"[+\-×÷*/^]")


def leaks(text: str, problem: Problem) -> bool:
    """True when the text states an accepted answer outside the problem itself.

    Numbers count anywhere but in the problem as written, so even a restatement
    ("repartir 16 entre 4" when 16 ÷ 4 = 4) is too close; expressions are read
    with operation words as symbols ("doce menos cinco" is 12 - 5).
    """
    answers = accepted_answers(problem)
    shown = digits_for_words(text).replace(problem.text, " ")
    if answers & set(extract_numbers(shown)):
        return True
    targets: list[sp.Expr] = [sp.Rational(a.numerator, a.denominator) for a in answers]
    return any(_equals(span, targets) for span in _spans(_plain(text, problem)))


def expressions(text: str, problem: Problem | None) -> set[str]:
    """The arithmetic written in the text ('12 - 5'), the problem itself left out."""
    return set(_spans(_plain(text, problem)))


def _plain(text: str, problem: Problem | None) -> str:
    """Digits for number words, symbols for operation words, the problem removed."""
    plain = normalize(digits_for_words(text))
    if problem is not None:
        plain = plain.replace(normalize(problem.text), " ")
    return _SENTENCE_END.sub(";", plain)


def _spans(plain: str) -> list[str]:
    return [_balanced(span) for span in _SPAN.findall(plain) if _OPERATOR.search(span)]


def _balanced(span: str) -> str:
    """Drops unmatched parentheses at the ends: '(x = 12 - 5)' gives '12 - 5'."""
    while span.startswith("(") and span.count("(") > span.count(")"):
        span = span[1:].lstrip()
    while span.endswith(")") and span.count(")") > span.count("("):
        span = span[:-1].rstrip()
    return span.strip()


def _equals(expression: str, targets: list[sp.Expr]) -> bool:
    if len(expression) > MAX_EXPRESSION_LENGTH:
        return True  # fails closed: no hint needs arithmetic this long
    try:
        value = safe_parse(expression)
    except PARSE_ERRORS:
        return False
    return any(are_values_equivalent(value, target) for target in targets)
