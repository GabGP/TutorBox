import re

import sympy as sp

EQUATION_PATTERN = re.compile(
    r"([0-9a-zA-Z\s\+\-\*/\(\)\^]+)\s*=\s*([0-9a-zA-Z\s\+\-\*/\(\)\^]+)"
)


def extract_linear_polynomial(
    question_text: str,
) -> tuple[sp.Poly, sp.Symbol] | None:
    """Extracts a linear polynomial and variable symbol from equation text."""
    for match in EQUATION_PATTERN.finditer(question_text):
        left_raw, right_raw = match.group(1).strip(), match.group(2).strip()
        tokens = re.findall(r"[\d\w\+\-\*/\(\)\^]+", left_raw)
        for i in range(len(tokens)):
            cand_left = re.sub(r"(\d)\s*([a-zA-Z\(])", r"\1*\2", " ".join(tokens[i:]))
            norm_right = re.sub(r"(\d)\s*([a-zA-Z\(])", r"\1*\2", right_raw)
            var_match = re.search(r"[a-zA-Z]", cand_left + norm_right)
            symbol = sp.Symbol(var_match.group(0) if var_match else "x")
            try:
                left_expr = sp.parse_expr(cand_left)
                right_expr = sp.parse_expr(norm_right)
                var_side = left_expr if symbol in left_expr.free_symbols else right_expr
                return sp.Poly(var_side, symbol), symbol
            except (sp.SympifyError, SyntaxError, TypeError, ValueError):
                continue
    return None


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
