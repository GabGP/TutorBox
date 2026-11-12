"""Hint levels 0 to 2 for one operation on two whole numbers (23 + 45, 7 × 8).

0 restates the goal with the child's numbers, 1 names the concept and 2 isolates
a smaller step: the units, counting on, one row less of the table. Level 3, the
worked example, is in hints.py. The wordings live in knowledge_base.json
(paraphrases, five per template); the code only picks the template and computes
its numbers. `p` is the problem's text, which picks the wording.
"""

from modes.socratic.knowledge import phrase

__all__ = ["LADDERS"]


def _suma(a: int, b: int, level: int, p: str) -> str:
    if level < 2:
        return phrase(f"suma_{level}", p, a=a, b=b)
    if a < 10 and b < 10:
        return phrase("suma_2_count", p, big=max(a, b), small=min(a, b))
    return phrase("suma_2_units", p, ua=a % 10, ub=b % 10)


def _resta(a: int, b: int, level: int, p: str) -> str:
    if level < 2:
        return phrase(f"resta_{level}", p, a=a, b=b)
    if a < 10:
        return phrase("resta_2_back", p, a=a, b=b)
    if a - b < 10:  # the units step (32 - 25 → 12 - 5) would be the whole answer
        return phrase("resta_2_up", p, a=a, b=b)
    units_a, units_b = a % 10, b % 10
    if units_a >= units_b:
        return phrase("resta_2_units", p, ua=units_a, ub=units_b)
    return phrase("resta_2_borrow", p, ua=units_a, ub=units_b, ten=units_a + 10)


def _multiplicacion(a: int, b: int, level: int, p: str) -> str | None:
    if level == 2 and b < 2:
        return None
    return phrase(f"multiplicacion_{level}", p, a=a, b=b, prev=b - 1)


def _division(a: int, b: int, level: int, p: str) -> str:
    return phrase(f"division_{level}", p, a=a, b=b, b2=b * 2)


LADDERS = {
    "suma": _suma,
    "resta": _resta,
    "multiplicacion": _multiplicacion,
    "division": _division,
}
