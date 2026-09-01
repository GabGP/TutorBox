from tokenize import TokenError

import sympy as sp

from src.math_engine.equation_parser import (
    EQUATION_PATTERN,
    PARSE_ERRORS,
    parse_equation_components,
)


def test_equation_pattern_matches_standard_equation():
    match = EQUATION_PATTERN.search("2x + 4 = 12")
    assert match is not None
    assert match.group(1).strip() == "2x + 4"
    assert match.group(2).strip() == "12"


def test_equation_pattern_no_match_for_plain_text():
    assert EQUATION_PATTERN.search("Solo texto sin ecuacion") is None


def test_parse_equation_components_standard_linear():
    result = parse_equation_components("2x + 4 = 12")
    assert result is not None
    left_expr, right_expr, variable_symbol = result
    assert left_expr is not None
    assert str(variable_symbol) == "x"
    assert right_expr == 12


def test_parse_equation_components_with_natural_language_prefix():
    result = parse_equation_components("¿Cuál es el valor de x en 3x + 6 = 21?")
    assert result is not None
    _left_expr, right_expr, variable_symbol = result
    assert str(variable_symbol) == "x"
    assert right_expr == 21


def test_parse_equation_components_with_parentheses():
    result = parse_equation_components("3(x + 2) = 15")
    assert result is not None
    left_expr, right_expr, variable_symbol = result
    assert left_expr is not None
    assert str(variable_symbol) == "x"
    assert right_expr == 15


def test_parse_equation_components_no_equation_returns_none():
    assert parse_equation_components("Solo texto") is None
    assert parse_equation_components("3 + 4 * 2") is None


def test_parse_equation_components_unparseable_returns_none():
    assert parse_equation_components("+++ = ---") is None
    assert parse_equation_components("x + = invalid") is None


def test_parse_errors_tuple_contains_expected_types():
    assert sp.SympifyError in PARSE_ERRORS
    assert SyntaxError in PARSE_ERRORS
    assert TypeError in PARSE_ERRORS
    assert ValueError in PARSE_ERRORS
    assert TokenError in PARSE_ERRORS


def test_parse_equation_components_different_variable():
    result = parse_equation_components("3y = 21")
    assert result is not None
    _, _, variable_symbol = result
    assert str(variable_symbol) == "y"
