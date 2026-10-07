"""Hint levels 2 and 3 for equations: a first step, then a solved parallel one."""

from fractions import Fraction

import pytest

from modes.socratic import equation_hints
from modes.socratic.equation_hints import equation_hint
from modes.socratic.problems import Problem, find_problem


@pytest.mark.parametrize(
    ("equation", "step"),
    [
        ("x + 5 = 12", "Cuenta desde 5 hasta llegar a 12. ¿Cuántos pasos das?"),
        ("9 + x = 17", "Cuenta desde 9 hasta llegar a 17. ¿Cuántos pasos das?"),
        ("n - 7 = 9", "Empieza en 9 y cuenta 7 hacia adelante. ¿A qué número llegas?"),
        (
            "__ × 32 = 192",
            (
                "¿Qué número multiplicado por 32 da 192? Prueba la tabla del 32: "
                "32 × 1 = 32, 32 × 2 = 64. ¿Sigues?"
            ),
        ),
        (
            "x ÷ 4 = 6",
            (
                "Si repartes un número entre 4 y a cada uno le tocan 6, piensa en 4 "
                "grupos de 6. ¿Cuántos hay en total?"
            ),
        ),
        (
            "2x + 4 = 14",
            "Primero deshaz el + 4: quita 4 de los dos lados. ¿Cuánto es 14 - 4?",
        ),
        (
            "5n - 3 = 27",
            "Primero deshaz el - 3: suma 3 a los dos lados. ¿Cuánto es 27 + 3?",
        ),
    ],
)
def test_level_2_names_the_first_step_without_taking_it(equation, step):
    assert equation_hint(find_problem(equation), 2) == step


@pytest.mark.parametrize(
    ("equation", "example"),
    [
        (
            "x + 5 = 12",
            "en x + 3 = 8 contamos desde 3 hasta 8: son 5 pasos, así que x = 5",
        ),
        (
            "n - 7 = 9",
            "en n - 2 = 4 contamos 2 hacia adelante desde 4: llegamos a 6, así que n = 6",
        ),
        (
            "3 × __ = 24",
            "en 3 × __ = 12 buscamos en la tabla del 3: 3 × 4 = 12, así que __ = 4",
        ),
        ("x ÷ 4 = 6", "en x ÷ 2 = 4 juntamos 2 grupos de 4: 2 × 4 = 8, así que x = 8"),
        (
            "2x + 4 = 14",
            (
                "en 2 × x + 1 = 7 quitamos 1 de los dos lados: 2 × x = 6; luego "
                "repartimos 6 entre 2: x = 3"
            ),
        ),
        (  # the first example's 2 × n = 6 would show the answer 6
            "5n - 3 = 27",
            (
                "en 4 × n - 7 = 29 sumamos 7 a los dos lados: 4 × n = 36; luego "
                "repartimos 36 entre 4: n = 9"
            ),
        ),
    ],
)
def test_level_3_solves_a_parallel_equation(equation, example):
    problem = find_problem(equation)

    assert equation_hint(problem, 3) == (
        f"Mira este ejemplo: {example}. Ahora te toca: ¿qué número va en "
        f"{problem.text}?"
    )


def test_level_3_never_works_the_childs_own_equation(monkeypatch):
    problem = find_problem("x + 3 = 8")  # the first example itself

    assert "en x + 4 = 6" in equation_hint(problem, 3)

    monkeypatch.setattr(equation_hints, "_EXAMPLES", ((1, 3, 5),))
    assert equation_hint(problem, 3) is None


@pytest.mark.parametrize(
    "problem",
    [
        find_problem("3 × (x + 2) = 15"),  # its numbers are not a, b and c
        find_problem("2x + 3x = 10"),
        find_problem("12 ÷ n = 3"),  # not linear in n
        find_problem("x ÷ 2 + 1 = 4"),  # no shape for it
        find_problem("x + 1/2 = 3"),
        Problem("x + 0.5 = 3", Fraction(5, 2), "ecuacion"),  # decimals
        Problem("2x = x + 3", Fraction(3), "ecuacion"),  # the unknown on both sides
        Problem("x × x = 4", Fraction(2), "ecuacion"),
        Problem("x = 5", Fraction(5), "ecuacion"),
        Problem("2x = 1/2", Fraction(1, 4), "ecuacion"),
        Problem("__", Fraction(1), "ecuacion"),
    ],
)
def test_other_equations_keep_the_generic_hint(problem):
    assert equation_hint(problem, 2) is None
