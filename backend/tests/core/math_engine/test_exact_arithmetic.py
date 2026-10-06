"""Exact arithmetic for a child's text (core/math_engine/exact_arithmetic.py)."""

from fractions import Fraction

import pytest

from core.math_engine import evaluate_exact


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("23 + 45", Fraction(68)),
        ("7 × 8", Fraction(56)),
        ("12 ÷ 4", Fraction(3)),
        ("17 ÷ 5", Fraction(17, 5)),
        ("2 + 3 × 4", Fraction(14)),
        ("(3 + 4) × 2", Fraction(14)),
        ("1/2 + 1/3", Fraction(5, 6)),
        ("0.1 + 0.2", Fraction(3, 10)),  # exact, unlike floats
        (".5 + 5.", Fraction(11, 2)),
        ("100 + 1.05", Fraction(2021, 20)),  # the zero after the point stays
        ("0.05 × 100", Fraction(5)),
        ("0.1234567890123456789 × 10000000000000000000", Fraction(1234567890123456789)),
        ("3 + -2", Fraction(1)),
        ("-(3 + 4)", Fraction(-7)),
        ("+3 + 1", Fraction(4)),
        ("007 + 3", Fraction(10)),  # not a Python literal, still a number
    ],
)
def test_evaluates_the_four_operations_exactly(expression, expected):
    assert evaluate_exact(expression) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "9××9××9",  # Python reads ×× as a power: a tower that never finishes
        "9**9**9",
        "2 // 3",
        "5 % 3",
        "2 ÷ 0",
        "0 ÷ 0",
        "x + 1",
        "abs(3)",
        "2(3 + 4)",
        "3 4",
        "1.2.3",
        "1e999999999",  # exponent notation would build a gigantic number
        "3j",
        "",
        "   ",
        "1 + " * 40 + "1",  # longer than any primaria problem
    ],
)
def test_anything_else_is_not_arithmetic(expression):
    assert evaluate_exact(expression) is None
