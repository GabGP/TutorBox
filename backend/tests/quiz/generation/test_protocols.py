"""Unit tests for topic-adaptive derivation protocols."""

from quiz.generation.protocols import (
    _ARITHMETIC_PROTOCOL,
    _DECIMALS_PERCENTAGES_PROTOCOL,
    _FRACTIONS_PROTOCOL,
    _PRE_ALGEBRA_ONE_STEP_PROTOCOL,
    _PRE_ALGEBRA_PROTOCOL,
    _PRE_ALGEBRA_TWO_STEP_PROTOCOL,
    _UNIVERSAL_PROTOCOL,
    ONE_STEP_RECOVERY_INSTRUCTION,
    get_derivation_protocol,
    get_structural_recovery_instruction,
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


def test_one_step_equations_returns_one_step_protocol():
    protocol = get_derivation_protocol("pre_algebra", "one_step_equations")
    assert protocol == _PRE_ALGEBRA_ONE_STEP_PROTOCOL
    assert "ONE-STEP EQUATION PROTOCOL" in protocol
    assert "x/a = c" in protocol
    assert "FORBIDDEN" in protocol
    assert "NEVER write ax + b = c" in protocol


def test_two_step_equations_returns_two_step_protocol():
    protocol = get_derivation_protocol("pre_algebra", "two_step_equations")
    assert protocol == _PRE_ALGEBRA_TWO_STEP_PROTOCOL
    assert "TWO-STEP EQUATION PROTOCOL" in protocol
    assert "ax + b = c" in protocol
    assert "non-trivial integer coefficient" in protocol


def test_pre_algebra_no_subconcept_returns_generic():
    assert get_derivation_protocol("pre_algebra") == _PRE_ALGEBRA_PROTOCOL


def test_default_no_args_returns_universal():
    assert get_derivation_protocol() == _UNIVERSAL_PROTOCOL


def test_unknown_subconcept_falls_back_to_generic_pre_algebra():
    result = get_derivation_protocol("pre_algebra", "unknown_subconcept")
    assert result == _PRE_ALGEBRA_PROTOCOL


def test_arithmetic_with_subconcept_ignores_subconcept():
    result = get_derivation_protocol("arithmetic", "order_of_operations")
    assert result == _ARITHMETIC_PROTOCOL


def test_get_structural_recovery_instruction_with_pedagogical_mismatch():
    errors = [
        "Pedagogical mismatch: subconcept 'one_step_equations' requires a 1-step equation"
    ]
    res = get_structural_recovery_instruction(errors)
    assert ONE_STEP_RECOVERY_INSTRUCTION in res
    assert "STRUCTURAL FIX" in res


def test_get_structural_recovery_instruction_with_one_step_keyword():
    errors = ["1-step equation expected"]
    res = get_structural_recovery_instruction(errors)
    assert ONE_STEP_RECOVERY_INSTRUCTION in res


def test_get_structural_recovery_instruction_unrelated_errors():
    errors = ["Schema violation", "Math verification failed"]
    res = get_structural_recovery_instruction(errors)
    assert res == ""
