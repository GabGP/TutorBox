"""Safe mathematical parser converting verified arithmetic/algebraic AST to SymPy expressions."""

import ast
import re

import sympy as sp

MAX_EXPRESSION_LENGTH: int = 100
MAX_EXPONENT: int = 6
MAX_OPERAND: int = 10**9

_ALLOWED_CHARS_PATTERN = re.compile(r"^[0-9a-zA-Z\s\+\-\*/\(\)\.]*$")
_DISALLOWED_DOT_PATTERN = re.compile(r"(?<!\d)\.(?!\d)")
_DECIMAL_COMMA_PATTERN = re.compile(r"(\d),(\d)")
_COLON_DIVISION_PATTERN = re.compile(r"(\d)\s*:\s*(\d)")
_IMPLICIT_MUL_DIGIT_PATTERN = re.compile(r"(\d)\s*([a-zA-Z\(])")
_IMPLICIT_MUL_PAREN_PATTERN = re.compile(r"(\))\s*([\d\([a-zA-Z])")
_VARIABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z]$")


def _ast_to_sympy(node: ast.AST) -> sp.Expr:
    if isinstance(node, ast.Expression):
        return _ast_to_sympy(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise TypeError("Boolean values are not valid mathematical expressions.")
        if isinstance(node.value, int):
            if abs(node.value) > MAX_OPERAND:
                raise ValueError(
                    f"Operand {node.value} exceeds maximum allowed size ({MAX_OPERAND})."
                )
            return sp.Integer(node.value)
        if isinstance(node.value, float):
            return sp.Float(node.value)
        raise TypeError(f"Unsupported constant type: {type(node.value).__name__}.")

    if isinstance(node, ast.Name):
        if not _VARIABLE_NAME_PATTERN.match(node.id):
            raise ValueError(
                f"Variable name '{node.id}' is invalid. Only single ASCII letters are permitted."
            )
        return sp.Symbol(node.id)

    if isinstance(node, ast.UnaryOp):
        operand = _ast_to_sympy(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}.")

    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Pow) and any(
            isinstance(inner, ast.Pow) for inner in ast.walk(node.left)
        ):
            # A power of a power multiplies exponents: MAX_EXPONENT no longer bounds it.
            raise ValueError("Nested powers are not supported.")
        left = _ast_to_sympy(node.left)
        if isinstance(node.op, ast.Pow):
            if (
                not isinstance(node.right, ast.Constant)
                or not isinstance(node.right.value, int)
                or isinstance(node.right.value, bool)
            ):
                raise TypeError("Exponent must be an integer constant.")
            exp = node.right.value
            if not (0 <= exp <= MAX_EXPONENT):
                raise ValueError(
                    f"Exponent {exp} exceeds safe limits (0 to {MAX_EXPONENT})."
                )
            return left**exp

        right = _ast_to_sympy(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if isinstance(left, sp.Integer) and isinstance(right, sp.Integer):
                return sp.Rational(left, right)
            return left / right
        raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}.")

    raise ValueError(f"Forbidden AST node in expression: {type(node).__name__}.")


def safe_parse(text: str) -> sp.Expr:
    """Safely parses mathematical expressions without calling eval or arbitrary code execution."""
    cleaned = text.strip()
    if not cleaned or len(cleaned) > MAX_EXPRESSION_LENGTH:
        raise ValueError("Expression is empty or exceeds maximum permitted length.")

    normalized = (
        cleaned.replace("÷", "/").replace("×", "*").replace("·", "*").replace("^", "**")
    )
    normalized = _DECIMAL_COMMA_PATTERN.sub(r"\1.\2", normalized)
    normalized = _COLON_DIVISION_PATTERN.sub(r"\1/\2", normalized)

    if not _ALLOWED_CHARS_PATTERN.match(normalized):
        raise ValueError("Expression contains forbidden characters.")

    if _DISALLOWED_DOT_PATTERN.search(normalized):
        raise ValueError("Expression contains invalid decimal point usage.")

    normalized = _IMPLICIT_MUL_DIGIT_PATTERN.sub(r"\1*\2", normalized)
    normalized = _IMPLICIT_MUL_PAREN_PATTERN.sub(r"\1*\2", normalized)

    tree = ast.parse(normalized, mode="eval")
    return _ast_to_sympy(tree)
