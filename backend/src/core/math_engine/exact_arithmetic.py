"""Exact +, -, × and ÷ on numbers, for text a child typed.

The tutor must not hand a child's message to a general evaluator. Python's parser
gives precedence and parentheses; only the four operations are evaluated, with
Fractions so decimals stay exact. Powers, names and calls are not arithmetic, so a
doubled "××" (which Python reads as a power) can never run away.
"""

import ast
import operator
import re
from fractions import Fraction

from core.math_engine.safe_parser import MAX_EXPRESSION_LENGTH

__all__ = ["evaluate_exact"]

_OPERATIONS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
# No letters: "1e999999999" would make Fraction build a gigantic number.
_ALLOWED = re.compile(r"[0-9\s+\-*/().]*")
_LEADING_ZEROS = re.compile(r"(?<![\d.])0+(?=\d)")  # "007" is not a Python literal


def evaluate_exact(expression: str) -> Fraction | None:
    """The exact value of a +, -, ×, ÷ expression, or None if it is anything else."""
    text = expression.replace("×", "*").replace("÷", "/").strip()
    if len(text) > MAX_EXPRESSION_LENGTH or not _ALLOWED.fullmatch(text):
        return None
    text = _LEADING_ZEROS.sub("", text)
    try:
        return _value(ast.parse(text, mode="eval").body, text)
    except (SyntaxError, ValueError, ZeroDivisionError, RecursionError):
        return None


def _value(node: ast.AST, text: str) -> Fraction:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        digits_as_typed = ast.get_source_segment(text, node)
        assert digits_as_typed is not None  # ast.parse locates every node
        return Fraction(digits_as_typed)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _value(node.operand, text)
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATIONS:
        operation = _OPERATIONS[type(node.op)]
        return operation(_value(node.left, text), _value(node.right, text))
    raise ValueError("Only +, -, × and ÷ on numbers are supported.")
