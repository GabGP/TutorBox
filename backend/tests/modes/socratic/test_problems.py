"""Problems in children's messages, solved exactly (modes/socratic/problems.py)."""

from fractions import Fraction

import pytest

from modes.socratic.problems import (
    Problem,
    accepted_answers,
    find_attempt,
    find_problem,
    normalize,
)


@pytest.mark.parametrize(
    ("message", "text", "target", "operation", "operands"),
    [
        ("¿cuánto es 23 + 45?", "23 + 45", 68, "suma", (23, 45)),
        ("8 menos 3", "8 - 3", 5, "resta", (8, 3)),
        ("7 por 8", "7 × 8", 56, "multiplicacion", (7, 8)),
        ("3x4", "3 × 4", 12, "multiplicacion", (3, 4)),
        ("12 dividido entre 4", "12 ÷ 4", 3, "division", (12, 4)),
        ("el doble de 8", "8 × 2", 16, "multiplicacion", (8, 2)),
        ("el triple de 4", "4 × 3", 12, "multiplicacion", (4, 3)),
        ("la mitad de 10", "10 ÷ 2", 5, "division", (10, 2)),
        ("la cuarta parte de 12", "12 ÷ 4", 3, "division", (12, 4)),
        ("5 más 3 más 2", "5 + 3 + 2", 10, "combinada", ()),
        ("(2 + 3) × 4", "(2 + 3) × 4", 20, "combinada", ()),
        ("(2 + 3) por 4", "(2 + 3) × 4", 20, "combinada", ()),
        ("3 por (2 + 1)", "3 × (2 + 1)", 9, "combinada", ()),
        ("(8 - 2) entre 3", "(8 - 2) ÷ 3", 2, "combinada", ()),
        ("(2+3)x4", "(2 + 3) × 4", 20, "combinada", ()),
        ("(2 + 3) mas 4", "(2 + 3) + 4", 9, "combinada", ()),
        ("(5 + 5) menos 3", "(5 + 5) - 3", 7, "combinada", ()),
        ("1/2 + 1/4", "1/2 + 1/4", Fraction(3, 4), "fracciones", ()),
        ("(1/2)+1/4", "(1/2) + 1/4", Fraction(3, 4), "fracciones", ()),
        ("10,000 - 2,500", "10,000 - 2,500", 7500, "resta", (10000, 2500)),
        ("20% de 50", "20% de 50", 10, "porcentaje", ()),
        ("x + 5 = 12", "x + 5 = 12", 7, "ecuacion", ()),
        ("cuánto vale x en 2x + 4 = 12", "2x + 4 = 12", 4, "ecuacion", ()),
        ("__ × 32 = 192", "__ × 32 = 192", 6, "ecuacion", ()),
        ("n + 7 = 10", "n + 7 = 10", 3, "ecuacion", ()),
        ("-3 + x = 5", "-3 + x = 5", 8, "ecuacion", ()),
        ("-x + 3 = 5", "-x + 3 = 5", -2, "ecuacion", ()),
        ("- x + 3 = 5", "x + 3 = 5", 2, "ecuacion", ()),
        ("3 × 4 = ?", "3 × 4", 12, "multiplicacion", (3, 4)),
        ("23 + 45 = 70", "23 + 45", 68, "suma", (23, 45)),
    ],
)
def test_find_problem(message, text, target, operation, operands):
    problem = find_problem(message)

    assert problem == Problem(text, Fraction(target), operation, operands)


def test_decimal_problems_remember_their_notation():
    problem = find_problem("0,5 + 0,25")

    assert problem.text == "0.5 + 0.25"
    assert problem.target == Fraction(3, 4)
    assert (problem.operation, problem.decimal) == ("decimales", True)


@pytest.mark.parametrize(
    "message",
    [
        "3/4",  # a number, not a problem
        "tengo 5 manzanas y 3 peras",
        "hola",
        "5 ÷ 0",
        "2 + (3",
        "99999999999 + 1",
        "1" + " + 1" * 40,  # longer than any primaria problem
        "x + y = 3",
        "x - x = 3",  # no solution
        "x × x = 2",  # not a rational solution
        "x" + " + 1" * 20 + " = 50",
        "9××9××9",  # Python would read ×× as a power: a tower that never ends
        "x+" + "(" * 11 + "9" + "××6)" * 11 + "=5",  # the same through an equation
        "×".join(f"(x+{k})××6" for k in range(1, 6)) + "=5",  # a degree-30 equation
        "x + 3××2 = 11",  # the tutor has no powers
        "x + 1 = 2.5",  # SymPy's equation parser would read = 2 and answer 1
    ],
)
def test_messages_without_a_solvable_problem(message):
    assert find_problem(message) is None


def test_find_attempt_reads_the_childs_result():
    problem, value = find_attempt("23 + 45 = 70")

    assert (problem.text, value) == ("23 + 45", 70)
    assert find_attempt("x + 5 = 12") is None  # an equation, not an attempt
    assert find_attempt("3 × 4 = ?") is None  # no result given
    assert find_attempt("es 68") is None
    assert find_attempt("hola = 5") is None  # nothing to judge on the left
    assert find_attempt("9××9 = 5") is None  # ×× is not a multiplication


def test_accepted_answers_include_the_quotient_of_a_division_with_remainder():
    assert accepted_answers(find_problem("17 entre 5")) == {
        Fraction(17, 5),
        Fraction(3),
    }
    assert accepted_answers(find_problem("16 entre 4")) == {Fraction(4)}


def test_normalize_writes_operations_as_symbols():
    text = normalize("Cuánto es 1,000,000 más 2,5 por 3")

    assert text == "cuanto es 1000000 + 2.5 × 3"
