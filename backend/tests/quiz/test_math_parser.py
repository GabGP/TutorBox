from src.quiz.math_parser import (
    are_values_equivalent,
    evaluate_arithmetic_expression,
    extract_and_solve_problem,
    parse_option_expression,
    solve_linear_equation,
)


def test_parse_option_expression():
    # Clean numeric & fractional
    assert parse_option_expression("4") == 4
    assert str(parse_option_expression("3/4")) == "3/4"
    assert parse_option_expression("x = 12") == 12
    assert parse_option_expression("x = -5") == -5

    # Spanish operators
    assert parse_option_expression("8 ÷ 2") == 4
    assert parse_option_expression("4 × 3") == 12
    assert parse_option_expression("2 · 5") == 10

    # Invalid strings safely return None
    assert parse_option_expression("+++ * invalid") is None
    assert parse_option_expression("Propiedad Conmutativa") is None


def test_are_values_equivalent():
    assert are_values_equivalent(None, 4) is False
    assert are_values_equivalent(4, None) is False
    assert are_values_equivalent(4, 4) is True
    assert are_values_equivalent(4.0, 4) is True
    assert are_values_equivalent("abc", "abc") is True
    assert are_values_equivalent("abc", "def") is False


def test_solve_linear_equation_standard_and_parentheses():
    # Standard linear equations
    assert solve_linear_equation("2x + 4 = 12") == 4
    assert solve_linear_equation("x - 7 = 15") == 22
    assert solve_linear_equation("3y = 21") == 7

    # Equations with parentheses
    assert solve_linear_equation("3(x + 2) = 15") == 3
    assert solve_linear_equation("2(x - 1) = 8") == 5

    # Text without solvable equation
    assert solve_linear_equation("Texto sin ecuacion") is None
    assert solve_linear_equation("x + = invalid") is None


def test_evaluate_arithmetic_standard_and_parentheses():
    assert evaluate_arithmetic_expression("3 + 4 * 2") == 11
    assert evaluate_arithmetic_expression("12 / 3 + 4 * 2") == 12
    assert evaluate_arithmetic_expression("4(5 - 2)") == 12

    # Malformed or text
    assert evaluate_arithmetic_expression("Solo texto") is None
    assert evaluate_arithmetic_expression("3 + + *") is None
    assert evaluate_arithmetic_expression("Calcula 3 + (4 * 5") is None


def test_extract_and_solve_problem():
    eq_sol, mode = extract_and_solve_problem("¿Cuál es el valor de x en 2x + 4 = 12?")
    assert mode == "equation"
    assert eq_sol == 4

    arith_sol, mode = extract_and_solve_problem("¿Cuánto es 10 + 5 * 2?")
    assert mode == "arithmetic"
    assert arith_sol == 20

    none_sol, mode = extract_and_solve_problem("¿Qué es un número primo?")
    assert mode == "none"
    assert none_sol is None
