"""Shared equation parsing utilities for the math engine.

Centralizes the equation-matching regex and the token-stripping
parser that both `parser.py` (solver) and `ast_algebra.py`
(structural inspector) previously duplicated independently.
"""

import re
from tokenize import TokenError

import sympy as sp

PARSE_ERRORS: tuple[type[Exception], ...] = (
    sp.SympifyError,
    SyntaxError,
    TypeError,
    ValueError,
    TokenError,
)

EQUATION_PATTERN = re.compile(
    r"([0-9a-zA-Z\s\+\-\*/\(\)\^]+)\s*=\s*([0-9a-zA-Z\s\+\-\*/\(\)\^]+)"
)

_IMPLICIT_MULTIPLICATION = re.compile(r"(\d)\s*([a-zA-Z\(])")
_TOKEN_PATTERN = re.compile(r"[\d\w\+\-\*/\(\)\^]+")
_VARIABLE_PATTERN = re.compile(r"[a-zA-Z]")


def parse_equation_components(
    question_text: str,
) -> tuple[sp.Expr, sp.Expr, sp.Symbol] | None:
    """Parses the first valid equation in question text into components.

    Returns ``(left_expression, right_expression, variable_symbol)``
    or ``None`` if no parseable equation is found.

    Uses progressive token-stripping on the left-hand side to tolerate
    natural-language prefixes in noisy SLM output (e.g. "el valor de
    x en 2x + 4 = 12" → strips until "2x + 4" parses successfully).
    """
    for match in EQUATION_PATTERN.finditer(question_text):
        left_raw = match.group(1).strip()
        right_raw = match.group(2).strip()
        normalized_right = _IMPLICIT_MULTIPLICATION.sub(r"\1*\2", right_raw).replace(
            "^", "**"
        )
        tokens = _TOKEN_PATTERN.findall(left_raw)
        for start_index in range(len(tokens)):
            normalized_left = _IMPLICIT_MULTIPLICATION.sub(
                r"\1*\2", " ".join(tokens[start_index:])
            ).replace("^", "**")
            variable_match = _VARIABLE_PATTERN.search(
                normalized_left + normalized_right
            )
            variable_symbol = sp.Symbol(
                variable_match.group(0) if variable_match else "x"
            )
            try:
                left_expr = sp.parse_expr(normalized_left)
                right_expr = sp.parse_expr(normalized_right)
                return left_expr, right_expr, variable_symbol
            except PARSE_ERRORS:
                continue
    return None
