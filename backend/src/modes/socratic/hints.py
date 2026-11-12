"""Deterministic Socratic hint ladder, levels 0 to 3.

0 restates the goal, 1 names the concept, 2 isolates a smaller step and 3 works a
parallel example with other numbers (docs/architecture/socratic-pedagogy.md).
Operations on two numbers have their own levels 0-2 (operation_hints.py) and
equations their own levels 2-3 (equation_hints.py). `hint` re-checks every text
with the containment check and falls back to a wording whose only numbers are
the problem's own.
"""

from modes.socratic.containment import leaks
from modes.socratic.equation_hints import equation_hint
from modes.socratic.knowledge import phrase
from modes.socratic.operation_hints import LADDERS
from modes.socratic.problems import Problem

__all__ = ["hint"]

_EXAMPLES = {  # operation: (how to compute it, parallel examples to work)
    "suma": (lambda c, d: c + d, ((12, 15), (21, 14), (13, 24))),
    "resta": (lambda c, d: c - d, ((18, 5), (27, 13), (35, 12))),
    "multiplicacion": (lambda c, d: c * d, ((3, 4), (2, 5), (4, 3))),
    "division": (lambda c, d: c // d, ((12, 3), (10, 2), (15, 5))),
}
_CONCEPT = ("fracciones", "decimales", "porcentaje", "ecuacion", "combinada")


def hint(problem: Problem, level: int) -> str:
    """The level-N hint for the problem; never states an accepted answer."""
    text = _specific(problem, level)
    if text is None or leaks(text, problem):
        text = _generic(problem.text, level)
    return text


def _generic(p: str, level: int) -> str:
    return phrase(f"generic_{level}", p, p=p)


def _specific(problem: Problem, level: int) -> str | None:
    if len(problem.operands) != 2:
        if problem.operation == "ecuacion" and level >= 2:
            return equation_hint(problem, level)
        if problem.operation in _CONCEPT and level == 1:
            return phrase(f"concept_{problem.operation}", problem.text, p=problem.text)
        return None
    a, b = problem.operands
    if level == 3:
        return _example(problem, a, b)
    return LADDERS[problem.operation](a, b, level, problem.text)


def _example(problem: Problem, a: int, b: int) -> str | None:
    """A worked example whose numbers do not give the child's answer away."""
    compute, pairs = _EXAMPLES[problem.operation]
    for c, d in pairs:
        sums = " + ".join([str(c)] * d)
        text = phrase(
            f"worked_{problem.operation}",
            problem.text,
            c=c,
            d=d,
            r=compute(c, d),
            sums=sums,
            p=problem.text,
        )
        if (c, d) != (a, b) and not leaks(text, problem):
            return text
    return None
