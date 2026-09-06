import re

MATH_EXPR_PATTERN = re.compile(r"[\d\(\)\-][\d\s\+\-\*/÷×·:\(\)\.\^a-zA-Z]+[\d\)]")
OPERATORS_PATTERN = re.compile(r"[+\-*/÷×·:]")


def validate_arithmetic_structure(
    question_text: str, subconcept: str, eval_mode: str
) -> list[str]:
    """Validates arithmetic precedence and operator constraints."""
    if eval_mode != "arithmetic":
        return [
            (
                f"Pedagogical mismatch: subconcept '{subconcept}' requires an arithmetic "
                f"expression, but received eval_mode '{eval_mode}'."
            )
        ]
    math_match = MATH_EXPR_PATTERN.search(question_text)
    math_expr = math_match.group(0).strip() if math_match else ""
    if re.search(r"[a-zA-Z]", math_expr):
        return [
            f"Pedagogical mismatch: arithmetic subconcept '{subconcept}' cannot contain variables."
        ]
    if subconcept == "order_of_operations":
        operators = OPERATORS_PATTERN.findall(math_expr)
        if len(operators) < 2 and not ("(" in math_expr and ")" in math_expr):
            return [
                (
                    "Pedagogical mismatch: subconcept 'order_of_operations' requires at least "
                    "2 operations or parentheses for order of precedence."
                )
            ]
    elif subconcept == "addition_subtraction" and any(
        sym in math_expr for sym in ["*", "/", "÷", "×", "·", ":"]
    ):
        return [
            "Pedagogical mismatch: subconcept 'addition_subtraction' cannot contain multiplication or division."
        ]
    elif subconcept == "multiplication_division" and not any(
        sym in math_expr for sym in ["*", "/", "÷", "×", "·", ":"]
    ):
        return [
            "Pedagogical mismatch: subconcept 'multiplication_division' requires multiplication or division."
        ]
    return []


def validate_fractions_structure(question_text: str, subconcept: str) -> list[str]:
    """Validates fractional expression presence."""
    if "/" not in question_text and "fracci" not in question_text.lower():
        return [
            f"Pedagogical mismatch: fractions subconcept '{subconcept}' must contain fractional expressions."
        ]
    return []


def validate_decimals_percentages_structure(
    question_text: str, subconcept: str, eval_mode: str
) -> list[str]:
    """Validates decimal and percentage format."""
    if (
        subconcept == "percentages"
        and eval_mode != "percentage"
        and "%" not in question_text
    ):
        return [
            "Pedagogical mismatch: subconcept 'percentages' requires a percentage expression with '%'."
        ]
    if subconcept == "decimal_operations" and not re.search(
        r"\d+[\.,]\d+", question_text
    ):
        return [
            "Pedagogical mismatch: subconcept 'decimal_operations' requires numbers with decimal places."
        ]
    return []
