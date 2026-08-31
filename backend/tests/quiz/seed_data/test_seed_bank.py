import pytest

from quiz.contracts.models import QuizQuestion
from quiz.contracts.taxonomy import (
    CURRICULUM_TAXONOMY,
    is_valid_subconcept,
    is_valid_topic,
)
from quiz.seed_data import (
    ARITHMETIC_ADD_QUESTIONS,
    ARITHMETIC_DIV_QUESTIONS,
    ARITHMETIC_MUL_QUESTIONS,
    ARITHMETIC_SUB_QUESTIONS,
    DECIMALS_QUESTIONS,
    FRACTIONS_ADD_QUESTIONS,
    FRACTIONS_MUL_DIV_QUESTIONS,
    FRACTIONS_SIMPLIFICATION_QUESTIONS,
    FRACTIONS_SUB_QUESTIONS,
    ORDER_OF_OPS_ADVANCED_QUESTIONS,
    ORDER_OF_OPS_BASIC_QUESTIONS,
    PERCENTAGES_QUESTIONS,
    PRE_ALGEBRA_LINEAR_ADD_QUESTIONS,
    PRE_ALGEBRA_LINEAR_MUL_QUESTIONS,
    PRE_ALGEBRA_TWO_STEP_A_QUESTIONS,
    PRE_ALGEBRA_TWO_STEP_B_QUESTIONS,
    SEED_QUESTIONS,
)
from quiz.validation.validator import SymPyMathValidator


def test_seed_bank_minimum_question_count():
    """Verifies that the seed question bank contains at least 50 diagnostic questions."""
    assert len(SEED_QUESTIONS) >= 50
    assert len(SEED_QUESTIONS) == 66


def test_seed_bank_unique_identifiers():
    """Verifies all questions have non-empty, unique identifiers."""
    question_ids = [q.id for q in SEED_QUESTIONS]
    assert len(question_ids) == len(set(question_ids))
    for q_id in question_ids:
        assert isinstance(q_id, str) and len(q_id) > 0


def test_seed_bank_topic_distribution():
    """Verifies question counts per topic meet milestone minimum thresholds."""
    arithmetic_count = (
        len(ARITHMETIC_ADD_QUESTIONS)
        + len(ARITHMETIC_SUB_QUESTIONS)
        + len(ARITHMETIC_MUL_QUESTIONS)
        + len(ARITHMETIC_DIV_QUESTIONS)
        + len(ORDER_OF_OPS_BASIC_QUESTIONS)
        + len(ORDER_OF_OPS_ADVANCED_QUESTIONS)
    )
    fractions_count = (
        len(FRACTIONS_ADD_QUESTIONS)
        + len(FRACTIONS_SUB_QUESTIONS)
        + len(FRACTIONS_MUL_DIV_QUESTIONS)
        + len(FRACTIONS_SIMPLIFICATION_QUESTIONS)
    )
    pre_algebra_count = (
        len(PRE_ALGEBRA_LINEAR_ADD_QUESTIONS)
        + len(PRE_ALGEBRA_LINEAR_MUL_QUESTIONS)
        + len(PRE_ALGEBRA_TWO_STEP_A_QUESTIONS)
        + len(PRE_ALGEBRA_TWO_STEP_B_QUESTIONS)
    )
    decimals_pct_count = len(DECIMALS_QUESTIONS) + len(PERCENTAGES_QUESTIONS)

    assert arithmetic_count >= 15
    assert fractions_count >= 15
    assert pre_algebra_count >= 15
    assert decimals_pct_count >= 10


def test_seed_bank_curriculum_taxonomy_compliance():
    """Verifies all questions strictly belong to recognized topics and subconcepts."""
    for question in SEED_QUESTIONS:
        assert is_valid_topic(question.topic), (
            f"Invalid topic '{question.topic}' in {question.id}"
        )
        assert is_valid_subconcept(question.topic, question.subconcept), (
            f"Invalid subconcept '{question.subconcept}' for topic '{question.topic}' in {question.id}"
        )

        recognized_misconceptions = set(
            CURRICULUM_TAXONOMY[question.topic][question.subconcept]
        )
        for opt_key, detail in question.distractors.items():
            assert detail.misconception in recognized_misconceptions, (
                f"Question {question.id} option {opt_key} has unrecognized misconception: "
                f"'{detail.misconception}'. Recognized: {recognized_misconceptions}"
            )
            assert len(detail.explanation.strip()) >= 5


@pytest.mark.parametrize("question", SEED_QUESTIONS, ids=lambda q: q.id)
def test_each_seed_question_passes_sympy_math_validation(
    question: QuizQuestion,
):
    """Verifies that each individual seed question is 100% mathematically valid under SymPy."""
    validator = SymPyMathValidator()
    result = validator.validate_question_math(question)
    assert result.is_valid is True, (
        f"Mathematical validation failed for question '{question.id}' ({question.question_text}): "
        f"{result.errors}"
    )
    assert len(result.errors) == 0
