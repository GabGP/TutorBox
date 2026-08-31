import re
from tokenize import TokenError
from typing import Any

import sympy as sp

PARSE_ERRORS = (sp.SympifyError, SyntaxError, TypeError, ValueError, TokenError)


def parse_option_expression(option_text: str) -> sp.Expr | None:
    """Extracts and parses a numeric or algebraic expression from option text."""
    normalized_text = (
        option_text.strip().replace("÷", "/").replace("×", "*").replace("·", "*")
    )
    normalized_text = re.sub(r"(\d),(\d)", r"\1.\2", normalized_text)
    normalized_text = re.sub(r"(\d)\s*:\s*(\d)", r"\1/\2", normalized_text)
    if equation_match := re.search(r"=\s*(-?\d+(?:/\d+)?(?:\.\d+)?)", normalized_text):
        normalized_text = equation_match.group(1)
    try:
        return sp.parse_expr(normalized_text)
    except PARSE_ERRORS:
        return None


def are_values_equivalent(expr_a: Any, expr_b: Any) -> bool:
    """Checks if two symbolic expressions or numbers are mathematically equivalent."""
    if expr_a is None or expr_b is None:
        return False
    try:
        return abs(float(expr_a) - float(expr_b)) < 1e-6
    except (TypeError, ValueError):
        pass
    try:
        return bool(sp.simplify(expr_a - expr_b) == 0)
    except (TypeError, ValueError, AttributeError):
        pass
    return str(expr_a).strip() == str(expr_b).strip()


def solve_linear_equation(question_text: str) -> sp.Expr | None:
    """Attempts to extract and solve a 1-variable linear equation (e.g. 2x + 4 = 12)."""
    equation_pattern = (
        r"([0-9a-zA-Z\s\+\-\*/\(\)\^]+)\s*=\s*([0-9a-zA-Z\s\+\-\*/\(\)\^]+)"
    )
    for match in re.finditer(equation_pattern, question_text):
        left_raw, right_raw = match.group(1).strip(), match.group(2).strip()
        tokens = re.findall(r"[\d\w\+\-\*/\(\)\^]+", left_raw)
        for i in range(len(tokens)):
            candidate_left = re.sub(
                r"(\d)\s*([a-zA-Z\(])", r"\1*\2", " ".join(tokens[i:])
            )
            normalized_right = re.sub(r"(\d)\s*([a-zA-Z\(])", r"\1*\2", right_raw)
            variable_match = re.search(r"[a-zA-Z]", candidate_left + normalized_right)
            variable_name = variable_match.group(0) if variable_match else "x"
            try:
                left_expr = sp.parse_expr(candidate_left)
                right_expr = sp.parse_expr(normalized_right)
                solutions = sp.solve(
                    sp.Eq(left_expr, right_expr), sp.Symbol(variable_name)
                )
                if solutions:
                    return solutions[0]
            except PARSE_ERRORS:
                pass
    return None


def evaluate_arithmetic_expression(question_text: str) -> sp.Expr | None:
    """Attempts to extract and evaluate an arithmetic expression (e.g. 3 + 4 * 2)."""
    arithmetic_pattern = r"[\d\(\)][\d\s\+\-\*/\(\)\.\^]+[\d\)]"
    for match in re.finditer(arithmetic_pattern, question_text):
        candidate_expression = re.sub(
            r"(\d)\s*([\(])", r"\1*\2", match.group(0).strip()
        )
        try:
            evaluated_expr = sp.parse_expr(candidate_expression)
            if evaluated_expr is not None and not evaluated_expr.is_symbol:
                return evaluated_expr
        except PARSE_ERRORS:
            pass
    return None


def evaluate_percentage_expression(question_text: str) -> sp.Expr | None:
    """Attempts to extract and evaluate a percentage expression (e.g. 20% de 50)."""
    percentage_pattern = r"(\d+(?:\.\d+)?)\s*%\s*(?:de|\*)\s*(\d+(?:\.\d+)?)"
    if match := re.search(percentage_pattern, question_text, re.IGNORECASE):
        percentage_value = float(match.group(1))
        base_value = float(match.group(2))
        computed = (percentage_value / 100.0) * base_value
        return (
            sp.Integer(int(computed)) if computed.is_integer() else sp.Float(computed)
        )
    return None


def extract_and_solve_problem(question_text: str) -> tuple[sp.Expr | None, str]:
    """Extracts math problem from text and computes expected solution truth."""
    normalized_text = (
        question_text.replace("¿", "")
        .replace("?", "")
        .replace("÷", "/")
        .replace("×", "*")
        .replace("·", "*")
        .strip()
    )
    normalized_text = re.sub(r"(\d),(\d)", r"\1.\2", normalized_text)
    normalized_text = re.sub(r"(\d)\s*:\s*(\d)", r"\1/\2", normalized_text)
    if (
        percentage_solution := evaluate_percentage_expression(normalized_text)
    ) is not None:
        return percentage_solution, "percentage"
    if (equation_solution := solve_linear_equation(normalized_text)) is not None:
        return equation_solution, "equation"
    if (
        arithmetic_solution := evaluate_arithmetic_expression(normalized_text)
    ) is not None:
        return arithmetic_solution, "arithmetic"
    return None, "none"
