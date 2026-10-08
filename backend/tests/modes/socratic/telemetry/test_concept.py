"""Concept labels of tutor turns (modes/socratic/telemetry/concept.py)."""

from fractions import Fraction

import pytest

from modes.quiz.contracts.taxonomy import is_valid_subconcept, is_valid_topic
from modes.socratic.bank import load_bank
from modes.socratic.curriculum import load_curriculum
from modes.socratic.problems import Problem, find_problem
from modes.socratic.telemetry.concept import Concept, concept_for

BANK = load_bank()
# find_problem also builds this problem, but a hand-built one pins the case: 1 ÷ x
# is not a polynomial in x, so the equation has no polynomial to classify.
MISSING_POLYNOMIAL = Problem("1 ÷ x = 2", Fraction(1, 2), "ecuacion")
# One example for every operation row of the table, plus each fraction sign branch.
PROBLEM_CONCEPTS = [
    ("7 + 5", Concept("arithmetic", "addition_subtraction", "suma_resta")),
    ("9 - 4", Concept("arithmetic", "addition_subtraction", "suma_resta")),
    ("7 × 8", Concept("arithmetic", "multiplication_division", "multiplicacion")),
    ("36 ÷ 4", Concept("arithmetic", "multiplication_division", "division")),
    (
        "2 + 3 × 4",
        Concept("arithmetic", "order_of_operations", "operaciones_combinadas"),
    ),
    ("1.5 + 2.25", Concept("decimals_percentages", "decimal_operations", "decimales")),
    (
        "20% de 50",
        Concept("decimals_percentages", "percentages", "razones_porcentajes"),
    ),
    ("1/2 + 1/4", Concept("fractions", "addition_subtraction", "fracciones")),
    ("1/2 - 1/4", Concept("fractions", "addition_subtraction", "fracciones")),
    ("(1/2)+1/4", Concept("fractions", "addition_subtraction", "fracciones")),
    ("1/2 × 3/4", Concept("fractions", "multiplication_division", "fracciones")),
    ("1/2 ÷ 3/4", Concept("fractions", "multiplication_division", "fracciones")),
    ("1/2 + 1/4 × 2", Concept("fractions", None, "fracciones")),
    (
        "x + 5 = 12",
        Concept("pre_algebra", "one_step_equations", "operaciones_combinadas"),
    ),
    (
        "2x + 3 = 11",
        Concept("pre_algebra", "two_step_equations", "operaciones_combinadas"),
    ),
]
TOPIC_CONCEPTS = [
    ("suma_resta", Concept("arithmetic", "addition_subtraction", "suma_resta")),
    (
        "multiplicacion",
        Concept("arithmetic", "multiplication_division", "multiplicacion"),
    ),
    ("division", Concept("arithmetic", "multiplication_division", "division")),
    (
        "operaciones_combinadas",
        Concept("arithmetic", "order_of_operations", "operaciones_combinadas"),
    ),
    ("fracciones", Concept("fractions", None, "fracciones")),
    ("decimales", Concept("decimals_percentages", "decimal_operations", "decimales")),
    (
        "razones_porcentajes",
        Concept("decimals_percentages", "percentages", "razones_porcentajes"),
    ),
]
EMITTED_CONCEPTS = (
    [expected for _message, expected in PROBLEM_CONCEPTS]
    + [expected for _topic_id, expected in TOPIC_CONCEPTS]
    + [concept_for(MISSING_POLYNOMIAL, None)]
)
EMITTED_PAIRS = sorted({(c.topic, c.subconcept) for c in EMITTED_CONCEPTS}, key=str)
EMITTED_CNB_TOPICS = sorted({c.cnb_topic for c in EMITTED_CONCEPTS if c.cnb_topic})


def _ids(item):
    return item.id


@pytest.mark.parametrize("item", BANK, ids=_ids)
def test_a_bank_problem_gets_the_labels_of_its_bank_entry(item):
    problem = find_problem(item.text)

    assert concept_for(problem, None) == Concept(item.topic, item.subconcept, item.cnb)


@pytest.mark.parametrize(("message", "expected"), PROBLEM_CONCEPTS)
def test_a_problem_outside_the_bank_gets_the_concept_of_its_operation(
    message, expected
):
    assert concept_for(find_problem(message), None) == expected


def test_an_equation_without_a_polynomial_has_no_subconcept():
    assert concept_for(MISSING_POLYNOMIAL, None) == Concept(
        "pre_algebra", None, "operaciones_combinadas"
    )


def test_an_operation_the_table_does_not_name_has_no_concept():
    unknown = Problem("2 ^ 3", Fraction(8), "a_future_operation")

    assert concept_for(unknown, None) == Concept()


@pytest.mark.parametrize(("topic_id", "expected"), TOPIC_CONCEPTS)
def test_a_topic_id_alone_gets_its_taxonomy_pair(topic_id, expected):
    assert concept_for(None, topic_id) == expected


def test_an_unmapped_topic_id_keeps_only_its_cnb_topic():
    assert concept_for(None, "geometria") == Concept(None, None, "geometria")


def test_a_turn_with_neither_a_problem_nor_a_topic_has_no_concept():
    assert concept_for(None, None) == Concept()


def test_a_problem_takes_precedence_over_the_topic_id():
    problem = find_problem("7 + 5")

    assert concept_for(problem, "fracciones") == Concept(
        "arithmetic", "addition_subtraction", "suma_resta"
    )


@pytest.mark.parametrize(("topic", "subconcept"), EMITTED_PAIRS)
def test_every_pair_the_tables_can_emit_is_in_the_quiz_taxonomy(topic, subconcept):
    if subconcept is None:
        assert is_valid_topic(topic)
    else:
        assert is_valid_subconcept(topic, subconcept)


@pytest.mark.parametrize("cnb_topic", EMITTED_CNB_TOPICS)
def test_every_cnb_topic_the_tables_can_emit_is_in_the_curriculum(cnb_topic):
    assert load_curriculum().get(cnb_topic) is not None
