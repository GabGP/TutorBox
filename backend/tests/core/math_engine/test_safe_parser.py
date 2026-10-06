"""Tests for safe_parser module protecting against RCE and DoS."""

import pytest
import sympy as sp

from core.math_engine.safe_parser import (
    MAX_EXPRESSION_LENGTH,
    safe_parse,
)


def test_safe_parse_numeric_constants():
    """Parses standard integers, decimals, and fractions safely."""
    assert safe_parse("4") == sp.Integer(4)
    assert safe_parse("-5") == sp.Integer(-5)
    assert safe_parse("+3") == sp.Integer(3)
    assert safe_parse("3.5") == sp.Float(3.5)
    assert safe_parse("3/4") == sp.Rational(3, 4)


def test_safe_parse_spanish_operators_and_notation():
    """Handles Spanish operators (÷, ×, ·), colon division, and decimal commas."""
    assert safe_parse("8 ÷ 2") == sp.Integer(4)
    assert safe_parse("4 × 3") == sp.Integer(12)
    assert safe_parse("2 · 5") == sp.Integer(10)
    assert safe_parse("12 : 3") == sp.Integer(4)
    assert safe_parse("3,5") == sp.Float(3.5)
    assert safe_parse("3,5 + 2,15") == sp.Float(5.65)


def test_safe_parse_algebraic_and_parentheses():
    """Supports single-letter variables, implicit multiplication, and grouped expressions."""
    x = sp.Symbol("x")
    y = sp.Symbol("y")
    assert safe_parse("x") == x
    assert safe_parse("-x") == -x
    assert safe_parse("2x + 4") == 2 * x + 4
    assert safe_parse("3*(x + 2)") == 3 * x + 6
    assert safe_parse("3(x + 2)") == 3 * x + 6
    assert safe_parse("3y") == 3 * y


def test_safe_parse_exponents():
    """Allows small non-negative integer exponents, but rejects large or chained powers."""
    x = sp.Symbol("x")
    assert safe_parse("x^2") == x**2
    assert safe_parse("2^3") == sp.Integer(8)
    assert safe_parse("x**2") == x**2

    # Reject exponent > MAX_EXPONENT (6)
    with pytest.raises(ValueError, match="exceeds safe limits"):
        safe_parse("2^7")
    with pytest.raises(ValueError, match="exceeds safe limits"):
        safe_parse("9**9")

    # Reject chained / non-constant exponents
    with pytest.raises((ValueError, TypeError)):
        safe_parse("9**9**9")
    with pytest.raises((ValueError, TypeError)):
        safe_parse("9××9××9")
    with pytest.raises((ValueError, TypeError)):
        safe_parse("x**y")


def test_safe_parse_rejects_rce_payloads():
    """Rejects Python attribute access, dunder methods, and function calls."""
    malicious_payloads = [
        "().__class__.__mro__[1].__name__",
        "__import__('os').system('id')",
        "eval('1+1')",
        "open('/etc/passwd')",
        "x.__class__",
        "().__class__",
        "[1, 2, 3]",
        "{'a': 1}",
    ]
    for payload in malicious_payloads:
        with pytest.raises((ValueError, SyntaxError)):
            safe_parse(payload)


def test_safe_parse_rejects_attribute_dots():
    """Prevents dot from being used for object attribute navigation."""
    with pytest.raises(ValueError, match="invalid decimal point"):
        safe_parse("x.y")
    with pytest.raises(ValueError, match="invalid decimal point"):
        safe_parse("a.b.c")


def test_safe_parse_length_and_character_restrictions():
    """Enforces strict length limits and character whitelisting."""
    with pytest.raises(ValueError, match="empty or exceeds"):
        safe_parse("")
    with pytest.raises(ValueError, match="empty or exceeds"):
        safe_parse("   ")
    with pytest.raises(ValueError, match="empty or exceeds"):
        safe_parse("1" * (MAX_EXPRESSION_LENGTH + 1))

    # Multi-letter variable names rejected
    with pytest.raises(ValueError, match="Only single ASCII letters"):
        safe_parse("variable")

    # Disallowed symbols rejected
    with pytest.raises(ValueError, match="forbidden characters"):
        safe_parse("2 $ 3")
    with pytest.raises(ValueError, match="forbidden characters"):
        safe_parse("x ; y")


def test_ast_to_sympy_defensive_branches():
    """Covers defensive fallback branches in AST converter."""
    import ast

    from core.math_engine.safe_parser import _ast_to_sympy

    # Boolean constants
    with pytest.raises(TypeError, match="Boolean"):
        _ast_to_sympy(ast.Constant(value=True))

    # Oversized operand
    with pytest.raises(ValueError, match="exceeds maximum"):
        _ast_to_sympy(ast.Constant(value=10**10))

    # Non numeric constant
    with pytest.raises(TypeError, match="Unsupported constant"):
        _ast_to_sympy(ast.Constant(value="text"))

    # Unsupported unary operator (e.g. Invert ~)
    with pytest.raises(ValueError, match="Unsupported unary"):
        _ast_to_sympy(ast.UnaryOp(op=ast.Invert(), operand=ast.Constant(value=1)))

    # Unsupported binary operator (e.g. BitOr |)
    with pytest.raises(ValueError, match="Unsupported binary"):
        _ast_to_sympy(
            ast.BinOp(
                left=ast.Constant(value=1),
                op=ast.BitOr(),
                right=ast.Constant(value=2),
            )
        )

    # Forbidden AST node
    with pytest.raises(ValueError, match="Forbidden AST node"):
        _ast_to_sympy(ast.Pass())
