"""Misconceptions in linear equations q·u + s = c, one step or two.

The equation is read the way equation_hints reads it: q is the coefficient of the
unknown u, s the constant on the same side and c the right side. One step and two
steps are told apart by is_two_step_linear, the test the concept mapper also uses.
"""

from fractions import Fraction

import sympy as sp

from core.math_engine import (
    exact_fraction,
    is_two_step_linear,
    parse_equation_components,
)
from modes.socratic.problems import Problem, sympy_equation

__all__ = ["equation_predictions"]


def equation_predictions(problem: Problem) -> list[tuple[str, Fraction | None]]:
    """The wrong values of the usual mistakes; none if the equation is not linear."""
    reading = _read_equation(problem)
    if reading is None:
        return []
    polynomial, q, s, c = reading
    if is_two_step_linear(polynomial):  # right answer (c - s) ÷ q
        return [
            ("forgot_division", c - s),
            ("divided_before_subtracting", c / q - s),
            ("subtracted_instead_of_divided", (c - s) - q),
            ("sign_inversion_error", (c + s) / q),
        ]
    if q == 1 and s != 0:  # x + 3 = 8: the child repeats the + instead of undoing it
        return [("wrong_inverse_operation", c + s)]
    if s == 0 and q != 1:  # 3x = 12: the child repeats the × instead of undoing it
        return [("wrong_inverse_operation", c * q)]
    return []


def _read_equation(
    problem: Problem,
) -> tuple[sp.Poly, Fraction, Fraction, Fraction] | None:
    """(the linear polynomial, q, s, c) as exact fractions; None if not readable so."""
    components = parse_equation_components(sympy_equation(problem.text))
    if components is None:
        return None
    left, right, unknown = components
    polynomial = left.as_poly(unknown)
    if polynomial is None or polynomial.degree() != 1:
        return None
    q, s, c = (exact_fraction(value) for value in (*polynomial.all_coeffs(), right))
    if q is None or s is None or c is None:
        return None
    return polynomial, q, s, c
