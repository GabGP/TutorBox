"""Names the misconception behind a child's wrong answer, from the answer alone.

Each operation has an ordered list of misconceptions (slugs of the quiz taxonomy).
Each one predicts the value a child would type after that mistake, and the first
prediction equal to the attempt names the error. The rules read only the problem and
the attempt, never the child's message, so one wrong answer always gets one label.
"""

from fractions import Fraction

from modes.socratic.problems import Problem
from modes.socratic.telemetry.error_rules_arithmetic import (
    addition_predictions,
    division_predictions,
    expression_predictions,
    multiplication_predictions,
    subtraction_predictions,
)
from modes.socratic.telemetry.error_rules_equations import equation_predictions
from modes.socratic.telemetry.error_rules_percentages_fractions import (
    fraction_predictions,
    percentage_predictions,
)

__all__ = ["ERROR_SLUGS", "UNCLASSIFIED", "classify_error"]

UNCLASSIFIED = "unclassified"
# The misconception slugs classify_error can return (UNCLASSIFIED is the other one).
ERROR_SLUGS = frozenset(
    {
        "added_denominators",
        "added_instead_of_subtracted",
        "alignment_error",
        "borrowing_error",
        "divided_before_subtracting",
        "forgot_division",
        "ignored_parentheses",
        "inverted_division",
        "left_to_right_precedence",
        "multiplied_by_percentage_directly",
        "sign_inversion_error",
        "subtracted_denominators",
        "subtracted_instead_of_divided",
        "subtracted_percentage_as_raw_number",
        "table_lookup_error",
        "wrong_inverse_operation",
    }
)

_PREDICTORS_BY_OPERATION = {
    "suma": addition_predictions,
    "resta": subtraction_predictions,
    "multiplicacion": multiplication_predictions,
    "division": division_predictions,
    "combinada": expression_predictions,
    "ecuacion": equation_predictions,
    "porcentaje": percentage_predictions,
    "fracciones": fraction_predictions,
}


def classify_error(problem: Problem, attempt: Fraction) -> str:
    """The misconception slug behind a WRONG answer, or UNCLASSIFIED.

    Precondition: the attempt is one the planner judged wrong, i.e. not in
    accepted_answers(problem). That is why a rule whose predicted value equals the
    right answer can never fire, so no guard for that case is written here.
    The problem comes from find_problem, which never builds a fraction with a zero
    denominator, so the fraction sum needs no guard for one either.
    """
    predict = _PREDICTORS_BY_OPERATION.get(problem.operation, _no_predictions)
    for slug, predicted in predict(problem):
        if predicted == attempt:
            return slug
    return UNCLASSIFIED


def _no_predictions(problem: Problem) -> list[tuple[str, Fraction | None]]:
    return []
