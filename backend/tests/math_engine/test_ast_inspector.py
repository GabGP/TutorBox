from src.math_engine.ast_inspector import (
    extract_linear_polynomial,
    validate_math_structure,
)


def test_ast_inspector_two_step_equation_valid():
    errors = validate_math_structure(
        question_text="¿Cuál es el valor de x en 2x + 4 = 12?",
        topic="pre_algebra",
        subconcept="two_step_equations",
        eval_mode="equation",
    )
    assert len(errors) == 0


def test_ast_inspector_two_step_rejects_arithmetic():
    errors = validate_math_structure(
        question_text="¿Cuál es el resultado de 3 + 4 * 2?",
        topic="pre_algebra",
        subconcept="two_step_equations",
        eval_mode="arithmetic",
    )
    assert any("requires an algebraic equation" in err for err in errors)


def test_ast_inspector_two_step_rejects_one_step_equation():
    errors = validate_math_structure(
        question_text="¿Cuál es el valor de x en x + 4 = 12?",
        topic="pre_algebra",
        subconcept="two_step_equations",
        eval_mode="equation",
    )
    assert any("requires a 2-step equation" in err for err in errors)


def test_ast_inspector_one_step_equation_valid():
    errors = validate_math_structure(
        question_text="¿Cuál es el valor de x en x + 5 = 12?",
        topic="pre_algebra",
        subconcept="one_step_equations",
        eval_mode="equation",
    )
    assert len(errors) == 0


def test_ast_inspector_one_step_rejects_two_step_equation():
    errors = validate_math_structure(
        question_text="¿Cuál es el valor de x en 2x + 4 = 12?",
        topic="pre_algebra",
        subconcept="one_step_equations",
        eval_mode="equation",
    )
    assert any("requires a 1-step equation" in err for err in errors)


def test_ast_inspector_order_of_operations_valid():
    errors = validate_math_structure(
        question_text="¿Cuál es el resultado de 3 + 4 * 2?",
        topic="arithmetic",
        subconcept="order_of_operations",
        eval_mode="arithmetic",
    )
    assert len(errors) == 0


def test_ast_inspector_order_of_operations_rejects_single_op():
    errors = validate_math_structure(
        question_text="¿Cuánto es 3 + 4?",
        topic="arithmetic",
        subconcept="order_of_operations",
        eval_mode="arithmetic",
    )
    assert any("requires at least 2 operations" in err for err in errors)


def test_ast_inspector_order_of_operations_with_parentheses():
    errors = validate_math_structure(
        question_text="¿Cuánto es (3 + 4)?",
        topic="arithmetic",
        subconcept="order_of_operations",
        eval_mode="arithmetic",
    )
    assert len(errors) == 0


def test_ast_inspector_arithmetic_rejects_variables():
    errors = validate_math_structure(
        question_text="¿Cuánto es 3x + 4?",
        topic="arithmetic",
        subconcept="addition_subtraction",
        eval_mode="arithmetic",
    )
    assert any("cannot contain variables" in err for err in errors)


def test_ast_inspector_addition_subtraction_rejects_multiplication():
    errors = validate_math_structure(
        question_text="¿Cuánto es 4 * 5?",
        topic="arithmetic",
        subconcept="addition_subtraction",
        eval_mode="arithmetic",
    )
    assert any("cannot contain multiplication" in err for err in errors)


def test_ast_inspector_multiplication_division_valid():
    errors = validate_math_structure(
        question_text="¿Cuánto es 6 * 7?",
        topic="arithmetic",
        subconcept="multiplication_division",
        eval_mode="arithmetic",
    )
    assert len(errors) == 0


def test_ast_inspector_multiplication_division_missing_symbol():
    errors = validate_math_structure(
        question_text="¿Cuánto es 6 + 7?",
        topic="arithmetic",
        subconcept="multiplication_division",
        eval_mode="arithmetic",
    )
    assert any("requires multiplication or division" in err for err in errors)


def test_ast_inspector_arithmetic_eval_mode_mismatch():
    errors = validate_math_structure(
        question_text="¿Cuánto es 3 + 4?",
        topic="arithmetic",
        subconcept="addition_subtraction",
        eval_mode="equation",
    )
    assert any("requires an arithmetic expression" in err for err in errors)


def test_ast_inspector_fractions_requires_slash():
    errors = validate_math_structure(
        question_text="¿Cuánto es 5 + 5?",
        topic="fractions",
        subconcept="addition_subtraction",
        eval_mode="arithmetic",
    )
    assert any("must contain fractional expressions" in err for err in errors)


def test_ast_inspector_percentages_requires_percent():
    errors = validate_math_structure(
        question_text="¿Cuánto es 20 de 50?",
        topic="decimals_percentages",
        subconcept="percentages",
        eval_mode="arithmetic",
    )
    assert any("requires a percentage expression" in err for err in errors)


def test_ast_inspector_decimals_requires_decimal_point():
    errors = validate_math_structure(
        question_text="¿Cuánto es 12 + 15?",
        topic="decimals_percentages",
        subconcept="decimal_operations",
        eval_mode="arithmetic",
    )
    assert any("requires numbers with decimal places" in err for err in errors)


def test_ast_inspector_pre_algebra_non_linear_degree():
    errors = validate_math_structure(
        question_text="¿Cuál es el valor de x en x^2 + 4 = 12?",
        topic="pre_algebra",
        subconcept="two_step_equations",
        eval_mode="equation",
    )
    assert any("equation must be linear" in err for err in errors)


def test_ast_inspector_pre_algebra_unparseable_equation():
    errors = validate_math_structure(
        question_text="¿Cuál es el valor de x en +++ = ---?",
        topic="pre_algebra",
        subconcept="two_step_equations",
        eval_mode="equation",
    )
    assert any("could not parse linear equation" in err for err in errors)


def test_ast_inspector_extract_polynomial_fallback():
    assert extract_linear_polynomial("No equation") is None
    assert extract_linear_polynomial("2/x + 4 = 12") is None


def test_ast_inspector_unknown_topic_returns_empty():
    assert validate_math_structure("x = 1", "unknown_topic", "sub", "equation") == []


def test_ast_inspector_colon_division_valid():
    errors = validate_math_structure(
        question_text="¿Cuánto es 6 : 2?",
        topic="arithmetic",
        subconcept="multiplication_division",
        eval_mode="arithmetic",
    )
    assert len(errors) == 0


def test_ast_inspector_colon_division_rejected_in_addition():
    errors = validate_math_structure(
        question_text="¿Cuánto es 6 : 2?",
        topic="arithmetic",
        subconcept="addition_subtraction",
        eval_mode="arithmetic",
    )
    assert any("cannot contain multiplication or division" in err for err in errors)


def test_ast_inspector_leading_negative_number_arithmetic():
    errors = validate_math_structure(
        question_text="¿Cuánto es -5 + 8?",
        topic="arithmetic",
        subconcept="addition_subtraction",
        eval_mode="arithmetic",
    )
    assert len(errors) == 0


def test_ast_inspector_fractions_word_matched():
    errors = validate_math_structure(
        question_text="¿Cuál de las siguientes fracciones es propia?",
        topic="fractions",
        subconcept="simplification",
        eval_mode="arithmetic",
    )
    assert len(errors) == 0
