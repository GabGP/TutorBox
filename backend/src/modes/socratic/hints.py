"""Deterministic Socratic hint ladder, levels 0 to 3.

0 restates the goal, 1 names the concept, 2 isolates a smaller step and 3 works a
parallel example with other numbers (docs/architecture/socratic-pedagogy.md).
Texts use the child's own numbers, sub-results and an example whose result is not
an accepted answer; `hint` re-checks each text with the leak guard and falls back
to a wording whose only numbers are the problem's own.
"""

from modes.socratic.guard import leaks
from modes.socratic.problems import Problem

__all__ = ["hint"]

_EXAMPLES = {  # operation: (how to compute it, parallel examples to work)
    "suma": (lambda c, d: c + d, ((12, 15), (21, 14), (13, 24))),
    "resta": (lambda c, d: c - d, ((18, 5), (27, 13), (35, 12))),
    "multiplicacion": (lambda c, d: c * d, ((3, 4), (2, 5), (4, 3))),
    "division": (lambda c, d: c // d, ((12, 3), (10, 2), (15, 5))),
}
_WORKED = {
    "suma": "Mira este ejemplo: {c} + {d} = {r}, porque juntamos {c} y {d}.",
    "resta": "Mira este ejemplo: {c} - {d} = {r}, porque a {c} le quitamos {d}.",
    "multiplicacion": "Mira este ejemplo: {c} × {d} es sumar {c}, {d} veces: "
    "{sums} = {r}.",
    "division": "Mira este ejemplo: {c} ÷ {d} = {r}, porque {d} × {r} = {c}.",
}
_CONCEPT = {
    "fracciones": "Mira los denominadores de {p}: ¿son iguales o diferentes? "
    "Eso te dice cómo empezar.",
    "decimales": "Con decimales, pon el punto debajo del punto: décimos con "
    "décimos. ¿Cómo quedan alineados los números de {p}?",
    "porcentaje": "Un porcentaje es una parte de cada 100. ¿Qué parte de 100 "
    "pide {p}, y cómo la buscarías?",
    "ecuacion": "En {p} buscamos el número que falta. ¿Qué operación deshace "
    "lo que le hicieron a ese número?",
    "combinada": "En {p} hay varias operaciones: primero los paréntesis, luego "
    "multiplicar y dividir, y al final sumar y restar. ¿Qué harías primero?",
}


def hint(problem: Problem, level: int) -> str:
    """The level-N hint for the problem; never states an accepted answer."""
    text = _specific(problem, level)
    if text is None or leaks(text, problem):
        text = _generic(problem.text, level)
    return text


def _generic(p: str, level: int) -> str:
    return (
        f"Vamos a resolver {p} paso a paso. ¿Qué te pide hacer este problema?",
        f"Piensa qué significa cada signo en {p}. ¿Qué vas a hacer primero?",
        f"Resuelve primero una parte pequeña de {p}. ¿Qué parte puedes hacer tú?",
        (
            f"Prueba con números más pequeños que se parezcan a {p} y luego "
            "vuelve a tu problema. ¿Qué números usarías?"
        ),
    )[level]


def _specific(problem: Problem, level: int) -> str | None:
    if len(problem.operands) != 2:
        concept = _CONCEPT.get(problem.operation)
        return concept.format(p=problem.text) if concept and level == 1 else None
    a, b = problem.operands
    if level == 3:
        return _example(problem, a, b)
    return _LADDERS[problem.operation](a, b, level)


def _example(problem: Problem, a: int, b: int) -> str | None:
    """A worked example whose numbers do not give the child's answer away."""
    compute, pairs = _EXAMPLES[problem.operation]
    for c, d in pairs:
        sums = " + ".join([str(c)] * d)
        worked = _WORKED[problem.operation].format(c=c, d=d, r=compute(c, d), sums=sums)
        text = f"{worked} Ahora intenta tú: ¿cuánto es {problem.text}?"
        if (c, d) != (a, b) and not leaks(text, problem):
            return text
    return None


def _suma(a: int, b: int, level: int) -> str:
    if level == 0:
        return (
            f"¡Vamos a pensarlo juntos! Queremos juntar {a} y {b}. ¿Por dónde empiezas?"
        )
    if level == 1:
        return (
            f"Sumar es juntar. Si tienes {a} y te dan {b} más, ¿cuántos tienes? "
            "Puedes separar cada número en decenas y unidades."
        )
    if a < 10 and b < 10:
        return f"Empieza en {max(a, b)} y cuenta {min(a, b)} más. ¿A qué número llegas?"
    return f"Empieza por las unidades: ¿cuánto es {a % 10} + {b % 10}?"


def _resta(a: int, b: int, level: int) -> str:
    if level == 0:
        return f"Vamos a pensar en {a} - {b}. ¿Qué pasa cuando a {a} le quitas {b}?"
    if level == 1:
        return (
            f"Restar es quitar. Si tienes {a} y quitas {b}, ¿cuántos quedan? "
            f"También puedes pensar: ¿qué número sumado a {b} da {a}?"
        )
    if a < 10:
        return f"Empieza en {a} y cuenta hacia atrás {b}. ¿A qué número llegas?"
    units_a, units_b = a % 10, b % 10
    if units_a >= units_b:
        return f"Empieza por las unidades: ¿cuánto es {units_a} - {units_b}?"
    return (
        f"Las unidades {units_a} son menos que {units_b}: pide prestada una "
        f"decena. ¿Cuánto es {units_a + 10} - {units_b}?"
    )


def _multiplicacion(a: int, b: int, level: int) -> str | None:
    if level == 0:
        return f"Vamos a pensar en {a} × {b}. ¿Qué significa multiplicar {a} por {b}?"
    if level == 1:
        return (
            f"Multiplicar es sumar el mismo número varias veces: {a} × {b} es "
            f"sumar {a}, {b} veces. ¿Cómo empezarías?"
        )
    if b < 2:
        return None
    return f"{a} × {b} es {a} × {b - 1} más otro {a}. ¿Cuánto es {a} × {b - 1}?"


def _division(a: int, b: int, level: int) -> str:
    if level == 0:
        return f"Vamos a pensar en {a} ÷ {b}. ¿Qué significa repartir {a} entre {b}?"
    if level == 1:
        return (
            f"Dividir es repartir en partes iguales. Si repartes {a} entre {b}, "
            f"¿cuántos le tocan a cada uno? Piensa en la tabla del {b}."
        )
    return (
        f"¿Qué número multiplicado por {b} da {a}? Prueba la tabla del {b}: "
        f"{b} × 1 = {b}, {b} × 2 = {b * 2}. ¿Sigues?"
    )


_LADDERS = {
    "suma": _suma,
    "resta": _resta,
    "multiplicacion": _multiplicacion,
    "division": _division,
}
