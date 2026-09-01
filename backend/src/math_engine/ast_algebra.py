import sympy as sp

from math_engine.equation_parser import parse_equation_components


def extract_linear_polynomial(
    question_text: str,
) -> tuple[sp.Poly, sp.Symbol] | None:
    """Extracts a linear polynomial and variable symbol from equation text."""
    components = parse_equation_components(question_text)
    if components is None:
        return None
    left_expr, right_expr, variable_symbol = components
    variable_side = (
        left_expr if variable_symbol in left_expr.free_symbols else right_expr
    )
    poly = variable_side.as_poly(variable_symbol)
    if poly is None:
        return None
    return poly, variable_symbol


def is_two_step_linear(poly: sp.Poly) -> bool:
    """Checks if polynomial corresponds to a 2-step equation (a not in {-1, 0, 1} and b != 0)."""
    coeffs = poly.all_coeffs()
    coeff_a = coeffs[0]
    coeff_b = coeffs[1] if len(coeffs) > 1 else sp.Integer(0)
    return (coeff_a not in {-1, 0, 1}) and (coeff_b != 0)


def validate_pre_algebra_structure(
    question_text: str, subconcept: str, eval_mode: str
) -> list[str]:
    """Validates pre-algebra equation structure and step count."""
    if eval_mode != "equation":
        return [
            (
                f"Pedagogical mismatch: subconcept '{subconcept}' requires an algebraic "
                f"equation with variable, but received eval_mode '{eval_mode}'."
            )
        ]
    poly_tuple = extract_linear_polynomial(question_text)
    if not poly_tuple:
        return [
            f"Pedagogical mismatch: could not parse linear equation for '{subconcept}'."
        ]
    poly, _ = poly_tuple
    if poly.degree() != 1:
        return [
            f"Pedagogical mismatch: equation must be linear (degree 1), got degree {poly.degree()}."
        ]
    two_step = is_two_step_linear(poly)
    if subconcept == "two_step_equations" and not two_step:
        return [
            (
                "Pedagogical mismatch: subconcept 'two_step_equations' requires a 2-step "
                "equation (ax + b = c with a not in {-1, 0, 1} and b != 0), but received a 1-step equation."
            )
        ]
    if subconcept == "one_step_equations" and two_step:
        return [
            (
                "Pedagogical mismatch: subconcept 'one_step_equations' requires a 1-step "
                "equation, but received a 2-step equation."
            )
        ]
    return []
