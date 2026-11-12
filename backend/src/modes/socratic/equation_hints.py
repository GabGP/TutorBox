"""Hint levels 2 and 3 for equations (the CNB's operación abierta).

For one-step (x + 5 = 12, n - 7 = 9, 3 × __ = 24, x ÷ 4 = 6) and two-step
(2x + 4 = 14) linear equations written with exactly the numbers SymPy finds in
them, level 2 names the first step to undo without doing it and level 3 solves a
parallel equation with other numbers. Anything else keeps the generic hint.
"""

from fractions import Fraction

from core.math_engine import exact_fraction, parse_equation_components
from modes.socratic.containment import leaks
from modes.socratic.knowledge import phrase
from modes.socratic.numbers import extract_numbers
from modes.socratic.problems import UNKNOWN, Problem, sympy_equation

__all__ = ["equation_hint"]

# (coefficient, constant, solution): x + 3 = 8, x - 2 = 4, 3 × x = 12... Two
# examples of each shape share no number, so one never gives an answer away.
_EXAMPLES = (
    *((1, 3, 5), (1, 4, 2), (1, -2, 6), (1, -3, 8)),
    *((3, 0, 4), (2, 0, 5), (Fraction(1, 2), 0, 8), (Fraction(1, 3), 0, 15)),
    *((2, 1, 3), (5, 4, 8), (2, -1, 3), (4, -7, 9)),
)


def equation_hint(problem: Problem, level: int) -> str | None:
    """Level 2 or 3 for a one- or two-step equation; None keeps the generic hint."""
    structure = _structure(problem)
    if structure is None:
        return None
    shape, unknown, numbers = structure
    if level == 2:
        return phrase(f"eq_step_{shape}", problem.text, **numbers)
    for q, s, x in _EXAMPLES:
        q, s = Fraction(q), Fraction(s)
        example = _numbers(q, s, q * x + s)
        if _shape(q, s) != shape or example == numbers:
            continue
        text = phrase(
            f"eq_worked_{shape}",
            problem.text,
            **example,
            u=unknown,
            x=x,
            p=problem.text,
        )
        if not leaks(text, problem):
            return text
    return None


def _structure(problem: Problem) -> tuple[str, str, dict[str, Fraction]] | None:
    """The shape of q·u + s = c, its unknown and its numbers, if written so."""
    parts = parse_equation_components(sympy_equation(problem.text))
    if parts is None:
        return None
    left, right, symbol = parts
    poly = left.as_poly(symbol)
    if poly is None or poly.degree() != 1:
        return None
    q, s, c = (exact_fraction(value) for value in (*poly.all_coeffs(), right))
    if q is None or s is None or c is None:
        return None
    shape = _shape(q, s)
    unknown = UNKNOWN.search(problem.text)  # none when the letter is not x or n
    if shape is None or unknown is None or s.denominator != 1 or c.denominator != 1:
        return None
    numbers = _numbers(q, s, c)
    said = [numbers["a"]] * (q != 1) + [abs(s)] * (s != 0) + [c]
    written = extract_numbers(UNKNOWN.sub(" ", problem.text))
    if sorted(written) != sorted(said):
        return None
    return shape, unknown.group(0), numbers


def _shape(q: Fraction, s: Fraction) -> str | None:
    if q == 1:
        return "suma" if s > 0 else "resta" if s < 0 else None
    if s == 0 and q.numerator == 1 and q.denominator > 1:
        return "cociente"
    if q.denominator == 1 and q > 1:
        return (
            "producto" if s == 0 else "dos_pasos_suma" if s > 0 else "dos_pasos_resta"
        )
    return None


def _numbers(q: Fraction, s: Fraction, c: Fraction) -> dict[str, Fraction]:
    a = q if q >= 1 else 1 / q
    return {"a": a, "a2": 2 * a, "b": abs(s), "c": c, "m": c - s}
