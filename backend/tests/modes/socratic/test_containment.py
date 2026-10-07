"""SymPy containment: no text states the answer, in any form (containment.py)."""

import pytest

from modes.socratic.containment import expressions, leaks
from modes.socratic.problems import find_problem

SUM = find_problem("23 + 45")  # 68
ONE_STEP = find_problem("x + 5 = 12")  # 7
TWO_STEP = find_problem("2x + 4 = 14")  # 5


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("La respuesta es 68.", SUM),
        ("Es sesenta y ocho.", SUM),  # in words
        ("Son 136/2.", SUM),  # a fraction equal to it
        ("Es 68.0", SUM),  # a decimal equal to it
        ("Es 60 + 8.", SUM),  # an expression equal to it
        ("Es 45 + 23.", SUM),  # the problem reordered is its value
        ("Es el doble de 34.", SUM),  # 34 × 2
        ("x = 7", ONE_STEP),  # an isolated assignment
        ("Vamos: x = 12 - 5. ¿Qué te pide?", ONE_STEP),  # assigned as an expression
        ("El número que buscas es 12 - 5.", ONE_STEP),
        ("Es doce menos cinco.", ONE_STEP),  # an expression in words
        ("Es 2^2 + 3.", ONE_STEP),  # a power, read by SymPy
        ("x = (14 - 4) ÷ 2", TWO_STEP),
        ("(x = 14 - 9)", TWO_STEP),  # unmatched parentheses around it
        ("Es ((3 + 2", TWO_STEP),
        ("12 ÷ 3 = 4, y ahora 16 ÷ 4", find_problem("16 entre 4")),
        ("Repartir 16 entre 4.", find_problem("16 entre 4")),  # its 4 is the answer
        ("Es 1/2.", find_problem("1/4 + 1/4")),
        ("Va a ser " + " + ".join(["1"] * 40), SUM),  # too long to check: blocked
    ],
)
def test_the_answer_in_any_form_leaks(text, problem):
    assert leaks(text, problem)


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("¿Cuánto es 23 + 45?", SUM),  # the problem itself
        ("Queremos juntar 23 y 45, x = 23 + 45.", SUM),  # so is restating it
        ("¿Cuánto es 3 + 5?", SUM),  # a smaller step
        ("Vamos a resolver x + 5 = 12 paso a paso.", ONE_STEP),
        ("Primero deshaz el + 4. ¿Cuánto es 14 - 4?", TWO_STEP),  # 10, not 5
        ("Tres cuartos es 3/4.", find_problem("1/4 + 1/4")),
        ("uno", find_problem("1,000,000 + 1")),  # an article, not a number
        ("Es 2 + (3", SUM),  # not arithmetic
    ],
)
def test_other_numbers_and_steps_do_not_leak(text, problem):
    assert not leaks(text, problem)


def test_expressions_read_operation_words_and_leave_the_problem_out():
    text = "¿Cuánto es 3 + 5? Luego doce menos cinco."

    assert expressions(text, SUM) == {"3 + 5", "12 - 5"}
    assert expressions("Juntamos 23 y 45: 23 más 45.", SUM) == set()
    assert expressions("Es 12 - 5.", None) == {"12 - 5"}
