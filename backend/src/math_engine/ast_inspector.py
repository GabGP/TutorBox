from math_engine.ast_algebra import (
    extract_linear_polynomial,
    is_two_step_linear,
    validate_pre_algebra_structure,
)
from math_engine.ast_arithmetic import (
    validate_arithmetic_structure,
    validate_decimals_percentages_structure,
    validate_fractions_structure,
)


def validate_math_structure(
    question_text: str, topic: str, subconcept: str, eval_mode: str
) -> list[str]:
    """Universal structural validator for mathematical expressions across Quiz and Socratic modes."""
    if topic == "pre_algebra":
        return validate_pre_algebra_structure(question_text, subconcept, eval_mode)
    if topic == "arithmetic":
        return validate_arithmetic_structure(question_text, subconcept, eval_mode)
    if topic == "fractions":
        return validate_fractions_structure(question_text, subconcept)
    if topic == "decimals_percentages":
        return validate_decimals_percentages_structure(
            question_text, subconcept, eval_mode
        )
    return []


__all__ = [
    "extract_linear_polynomial",
    "is_two_step_linear",
    "validate_math_structure",
]
