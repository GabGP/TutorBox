"""Unit tests for topic-adaptive derivation protocols."""

from quiz.generation.protocols import (
    _ARITHMETIC_PROTOCOL,
    _DECIMALS_PERCENTAGES_PROTOCOL,
    _FRACTIONS_PROTOCOL,
    _PRE_ALGEBRA_PROTOCOL,
    _UNIVERSAL_PROTOCOL,
    get_derivation_protocol,
)


def test_get_derivation_protocol_pre_algebra():
    protocol = get_derivation_protocol("pre_algebra")
    assert protocol == _PRE_ALGEBRA_PROTOCOL
    assert "MANDATORY PRE-ALGEBRA REVERSE-ENGINEERING PROTOCOL" in protocol
    assert "Step 1 (Target Root)" in protocol
    assert "Step 2 (Coefficients)" in protocol
    assert "Step 3 (Assemble Equation)" in protocol


def test_get_derivation_protocol_arithmetic():
    protocol = get_derivation_protocol("arithmetic")
    assert protocol == _ARITHMETIC_PROTOCOL
    assert "MANDATORY ARITHMETIC REVERSE-ENGINEERING PROTOCOL" in protocol
    assert "Step 1 (Target Value)" in protocol
    assert "Step 2 (Construct Expression)" in protocol
    assert "precedence" in protocol


def test_get_derivation_protocol_fractions():
    protocol = get_derivation_protocol("fractions")
    assert protocol == _FRACTIONS_PROTOCOL
    assert "MANDATORY FRACTIONS REVERSE-ENGINEERING PROTOCOL" in protocol
    assert "Step 1 (Target Fraction)" in protocol
    assert "denominators" in protocol


def test_get_derivation_protocol_decimals_percentages():
    protocol = get_derivation_protocol("decimals_percentages")
    assert protocol == _DECIMALS_PERCENTAGES_PROTOCOL
    assert "MANDATORY DECIMALS & PERCENTAGES REVERSE-ENGINEERING PROTOCOL" in protocol
    assert "Step 1 (Target Value)" in protocol
    assert "decimal" in protocol


def test_get_derivation_protocol_fallback():
    assert get_derivation_protocol(None) == _UNIVERSAL_PROTOCOL
    assert get_derivation_protocol("calculus") == _UNIVERSAL_PROTOCOL
    assert "MANDATORY REVERSE-ENGINEERING PROTOCOL" in _UNIVERSAL_PROTOCOL
    assert "Step 1 (Target Truth)" in _UNIVERSAL_PROTOCOL
