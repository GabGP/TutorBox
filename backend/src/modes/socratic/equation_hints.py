"""Hint levels 2 and 3 for equations (the CNB's operación abierta).

For one-step (x + 5 = 12, n - 7 = 9, 3 × __ = 24, x ÷ 4 = 6) and two-step
(2x + 4 = 14) linear equations written with exactly the numbers SymPy finds in
them, level 2 names the first step to undo without doing it and level 3 solves a
parallel equation with other numbers. Anything else keeps the generic hint.
"""

from fractions import Fraction

from core.math_engine import exact_fraction, parse_equation_components
from modes.socratic.containment import leaks
from modes.socratic.numbers import extract_numbers
from modes.socratic.problems import UNKNOWN, Problem, sympy_equation

__all__ = ["equation_hint"]

_STEP = {  # level 2: where to start, never the result
    "suma": "Cuenta desde {b} hasta llegar a {c}. ¿Cuántos pasos das?",
    "resta": "Empieza en {c} y cuenta {b} hacia adelante. ¿A qué número llegas?",
    "producto": "¿Qué número multiplicado por {a} da {c}? Prueba la tabla del {a}: "
    "{a} × 1 = {a}, {a} × 2 = {a2}. ¿Sigues?",
    "cociente": "Si repartes un número entre {a} y a cada uno le tocan {c}, piensa "
    "en {a} grupos de {c}. ¿Cuántos hay en total?",
    "dos_pasos_suma": "Primero deshaz el + {b}: quita {b} de los dos lados. "
    "¿Cuánto es {c} - {b}?",
    "dos_pasos_resta": "Primero deshaz el - {b}: suma {b} a los dos lados. "
    "¿Cuánto es {c} + {b}?",
}
_WORKED = {  # level 3: a parallel equation, solved
    "suma": "en {u} + {b} = {c} contamos desde {b} hasta {c}: son {x} pasos, así "
    "que {u} = {x}",
    "resta": "en {u} - {b} = {c} contamos {b} hacia adelante desde {c}: llegamos a "
    "{x}, así que {u} = {x}",
    "producto": "en {a} × {u} = {c} buscamos en la tabla del {a}: {a} × {x} = {c}, "
    "así que {u} = {x}",
    "cociente": "en {u} ÷ {a} = {c} juntamos {a} grupos de {c}: {a} × {c} = {x}, así "
    "que {u} = {x}",
    "dos_pasos_suma": "en {a} × {u} + {b} = {c} quitamos {b} de los dos lados: "
    "{a} × {u} = {m}; luego repartimos {m} entre {a}: {u} = {x}",
    "dos_pasos_resta": "en {a} × {u} - {b} = {c} sumamos {b} a los dos lados: "
    "{a} × {u} = {m}; luego repartimos {m} entre {a}: {u} = {x}",
}  # one sentence each: a reworded hint keeps at most three (guard.clean)
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
        return _STEP[shape].format(**numbers)
    for q, s, x in _EXAMPLES:
        q, s = Fraction(q), Fraction(s)
        example = _numbers(q, s, q * x + s)
        if _shape(q, s) != shape or example == numbers:
            continue
        worked = _WORKED[shape].format(**example, u=unknown, x=x)
        text = f"Mira este ejemplo: {worked}. Ahora te toca: ¿qué número va en "
        text += f"{problem.text}?"
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
