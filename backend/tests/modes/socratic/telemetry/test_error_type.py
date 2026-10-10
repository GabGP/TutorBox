"""Misconception labels for wrong answers (telemetry/error_type.py)."""

from fractions import Fraction

import pytest

from modes.quiz.contracts.taxonomy import CURRICULUM_TAXONOMY
from modes.socratic.planner import plan
from modes.socratic.problems import Problem, find_problem
from modes.socratic.state import Conversation
from modes.socratic.telemetry.error_type import (
    ERROR_SLUGS,
    UNCLASSIFIED,
    classify_error,
)
from tests.conftest import required

# (problem as the child typed it, the wrong answer, the misconception behind it)
LABELLED = [
    ("52 - 17", 69, "added_instead_of_subtracted"),
    ("52 - 17", 45, "borrowing_error"),
    ("98 - 9", 8, "alignment_error"),
    ("5 + 23", 73, "alignment_error"),
    ("23 + 5", 73, "alignment_error"),
    ("7 × 8", 48, "table_lookup_error"),
    ("12 ÷ 4", Fraction(1, 3), "inverted_division"),
    ("(2 + 3) × 4", 14, "ignored_parentheses"),
    ("2 + 3 × 4", 20, "left_to_right_precedence"),
    ("1000 + 2 × 3", 3006, "left_to_right_precedence"),
    ("1/2 + 1/3", Fraction(2, 5), "added_denominators"),
    ("1 / 2 + 1/3", Fraction(2, 5), "added_denominators"),
    ("1000/3 + 1/2", Fraction(1001, 5), "added_denominators"),
    ("3/4 - 1/2", 1, "subtracted_denominators"),
    ("x + 3 = 8", 11, "wrong_inverse_operation"),
    ("x - 3 = 8", 5, "wrong_inverse_operation"),
    ("3x = 12", 36, "wrong_inverse_operation"),
    ("x ÷ 4 = 6", Fraction(3, 2), "wrong_inverse_operation"),
    ("2x + 4 = 14", 10, "forgot_division"),
    ("2x + 4 = 14", 3, "divided_before_subtracting"),
    ("2x + 4 = 14", 8, "subtracted_instead_of_divided"),
    ("2x + 4 = 14", 9, "sign_inversion_error"),
    ("20% de 50", 1000, "multiplied_by_percentage_directly"),
    ("20% de 50", 30, "subtracted_percentage_as_raw_number"),
]

# The same kinds of problem with answers that no rule predicts, or no rule applies
UNLABELLED = [
    ("52 - 17", 70, UNCLASSIFIED),  # 52 + 17 + 1: no misconception behind it
    ("52 - 17", 43, UNCLASSIFIED),
    ("52 - 17", -118, UNCLASSIFIED),  # 52 - 170: same digit count, nothing shifted
    ("98 - 9", 9, UNCLASSIFIED),
    ("23 + 45", 473, UNCLASSIFIED),  # 23 + 450: the digits are already lined up
    ("13 × 8", 96, UNCLASSIFIED),  # 12 × 8: 13 is past the times table
    ("0 × 5", 5, UNCLASSIFIED),  # 1 × 5: zero is outside the times table
    ("12 ÷ 4", 4, UNCLASSIFIED),
    ("0 ÷ 5", 5, UNCLASSIFIED),  # would be 5 ÷ 0
    ("(2 + 3) × 4", 17, UNCLASSIFIED),
    ("2 + 3 × 4", 15, UNCLASSIFIED),
    ("1/2 + 1/3", Fraction(1, 3), UNCLASSIFIED),
    ("3/4 - 1/2", 2, UNCLASSIFIED),
    ("1/3 - 1/3", 1, UNCLASSIFIED),  # equal denominators: no prediction
    ("x + 3 = 8", 9, UNCLASSIFIED),
    ("3x = 12", 9, UNCLASSIFIED),
    ("x = 5", 3, UNCLASSIFIED),  # one step, but there is nothing to undo
    ("10 - x = 3", 13, UNCLASSIFIED),  # c + s, but the coefficient of x is -1
    ("1/x + 4 = 14", 2, UNCLASSIFIED),  # not a linear equation
    ("2x + 4 = 14", 6, UNCLASSIFIED),
    ("20% de 50", 40, UNCLASSIFIED),
    ("20% de 50", 25, UNCLASSIFIED),
    ("1.5 + 2", 2, UNCLASSIFIED),  # decimals have no rules
    ("1/2 + 1/3 + 1/4", 1, UNCLASSIFIED),  # three fractions
    ("1/2 ÷ 3", Fraction(3, 2), UNCLASSIFIED),  # only + and - join fractions
]

# Two misconceptions predict the same wrong answer: the earlier one in the list wins
RULE_ORDER = [
    ("10 - 5", 15, "added_instead_of_subtracted"),  # borrowing_error also gives 15
    ("2x - 4 = 0", 4, "forgot_division"),  # divided_before_subtracting also gives 4
    ("2x + 1 = 7", 4, "subtracted_instead_of_divided"),  # sign_inversion also gives 4
]


def _classify(text: str, attempt: Fraction) -> str:
    problem = find_problem(text)
    assert problem is not None, text
    return classify_error(problem, attempt)


@pytest.mark.parametrize(("text", "attempt", "slug"), LABELLED)
def test_a_wrong_answer_gets_the_misconception_behind_it(text, attempt, slug):
    assert _classify(text, Fraction(attempt)) == slug


@pytest.mark.parametrize(("text", "attempt", "slug"), UNLABELLED)
def test_an_answer_no_rule_predicts_stays_unclassified(text, attempt, slug):
    assert _classify(text, Fraction(attempt)) == slug


@pytest.mark.parametrize(("text", "attempt", "slug"), RULE_ORDER)
def test_the_earlier_rule_wins_when_two_predict_the_same_answer(text, attempt, slug):
    assert _classify(text, Fraction(attempt)) == slug


def test_every_error_slug_is_a_slug_of_the_curriculum_taxonomy():
    taxonomy_slugs = {
        slug
        for subconcepts in CURRICULUM_TAXONOMY.values()
        for slugs in subconcepts.values()
        for slug in slugs
    }

    assert ERROR_SLUGS <= taxonomy_slugs


def test_the_error_slugs_are_exactly_the_slugs_the_tests_observe():
    observed = {slug for _, _, slug in LABELLED + RULE_ORDER}

    assert observed == ERROR_SLUGS


@pytest.mark.parametrize("operation", ["suma", "resta", "multiplicacion", "division"])
def test_a_two_number_rule_without_two_operands_is_unclassified(operation):
    problem = Problem("52 - 17", Fraction(35), operation)  # operands left empty

    assert classify_error(problem, Fraction(45)) == UNCLASSIFIED


def test_an_expression_that_is_not_a_chain_of_numbers_is_unclassified():
    problem = Problem("2 + 3 ?", Fraction(5), "combinada")

    assert classify_error(problem, Fraction(9)) == UNCLASSIFIED


def test_reading_left_to_right_stops_at_a_division_by_zero():
    problem = Problem("8 ÷ 0 + 2", Fraction(0), "combinada")

    assert classify_error(problem, Fraction(2)) == UNCLASSIFIED


@pytest.mark.parametrize("text", ["2x + 4", "2x + 4 = x", "x**2 + 4 = 14"])
def test_an_equation_that_is_not_linear_in_numbers_is_unclassified(text):
    problem = Problem(text, Fraction(0), "ecuacion")

    assert classify_error(problem, Fraction(3)) == UNCLASSIFIED


def test_a_percentage_written_in_another_shape_is_unclassified():
    problem = Problem("twenty percent of 50", Fraction(10), "porcentaje")

    assert classify_error(problem, Fraction(1000)) == UNCLASSIFIED


def test_a_turn_from_the_planner_is_labelled_by_its_attempt_and_problem():
    _, conversation = plan(Conversation(), "2x + 4 = 14")
    move, _ = plan(conversation, "10")

    assert (move.kind, move.is_correct) == ("hint", False)
    error_type = classify_error(required(move.problem), required(move.attempt))
    assert error_type == "forgot_division"
