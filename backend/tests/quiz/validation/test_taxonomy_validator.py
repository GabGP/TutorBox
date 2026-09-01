import pytest

from src.quiz.contracts.models import DistractorDetail, QuizQuestion
from src.quiz.validation.taxonomy_validator import TaxonomyValidator


@pytest.fixture
def valid_two_step_question() -> QuizQuestion:
    return QuizQuestion(
        id="q_test_two_step",
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text="¿Cuál es el valor de x en 2x + 4 = 12?",
        options={"A": "4", "B": "8", "C": "3", "D": "6"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="forgot_division",
                explanation="Restaste 4 de 12 pero olvidaste dividir entre 2.",
            ),
            "C": DistractorDetail(
                misconception="subtracted_instead_of_divided",
                explanation="Restaste 2 en vez de dividir 8 entre 2.",
            ),
            "D": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Dividiste 12 entre 2 antes de restar 4.",
            ),
        },
    )


def test_taxonomy_validator_valid_question(valid_two_step_question: QuizQuestion):
    validator = TaxonomyValidator()
    result = validator.validate_question_taxonomy(
        valid_two_step_question,
        expected_topic="pre_algebra",
        expected_subconcept="two_step_equations",
    )
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_taxonomy_validator_topic_mismatch(valid_two_step_question: QuizQuestion):
    validator = TaxonomyValidator()
    result = validator.validate_question_taxonomy(
        valid_two_step_question,
        expected_topic="arithmetic",
        expected_subconcept="order_of_operations",
    )
    assert result.is_valid is False
    assert any("Topic mismatch: requested 'arithmetic'" in err for err in result.errors)


def test_taxonomy_validator_subconcept_mismatch(
    valid_two_step_question: QuizQuestion,
):
    validator = TaxonomyValidator()
    result = validator.validate_question_taxonomy(
        valid_two_step_question,
        expected_topic="pre_algebra",
        expected_subconcept="one_step_equations",
    )
    assert result.is_valid is False
    assert any(
        "Subconcept mismatch: requested 'one_step_equations'" in err
        for err in result.errors
    )


def test_taxonomy_validator_unrecognized_subconcept():
    invalid_sub_question = QuizQuestion(
        id="q_invalid_sub",
        topic="arithmetic",
        subconcept="quantum_arithmetic",
        question_text="¿Cuánto es 2 + 2?",
        options={"A": "4", "B": "5", "C": "6", "D": "7"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="sign_error", explanation="Error en signo."
            ),
            "C": DistractorDetail(
                misconception="borrowing_error", explanation="Error al pedir prestado."
            ),
            "D": DistractorDetail(
                misconception="alignment_error", explanation="Error de alineación."
            ),
        },
    )
    validator = TaxonomyValidator()
    result = validator.validate_question_taxonomy(
        invalid_sub_question,
        expected_topic="arithmetic",
        expected_subconcept=None,
    )
    assert result.is_valid is False
    assert any(
        "Subconcept 'quantum_arithmetic' is not recognized" in err
        for err in result.errors
    )


def test_taxonomy_validator_invalid_misconception_slug():
    question_with_bad_slug = QuizQuestion(
        id="q_bad_slug",
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text="¿Cuál es el valor de x en 2x + 4 = 12?",
        options={"A": "4", "B": "8", "C": "3", "D": "6"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="multiplied_all",
                explanation="Multiplicaste todo.",
            ),
            "C": DistractorDetail(
                misconception="subtracted_instead_of_divided",
                explanation="Restaste 2 en vez de dividir 8 entre 2.",
            ),
            "D": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Dividiste 12 entre 2 antes de restar 4.",
            ),
        },
    )
    validator = TaxonomyValidator()
    result = validator.validate_question_taxonomy(
        question_with_bad_slug,
        expected_topic="pre_algebra",
        expected_subconcept="two_step_equations",
    )
    assert result.is_valid is False
    assert any(
        "Misconception 'multiplied_all' on option 'B' is invalid for subconcept 'two_step_equations'"
        in err
        for err in result.errors
    )


def test_taxonomy_validator_general_topic_misconception_pool():
    question = QuizQuestion(
        id="q_general_pool",
        topic="arithmetic",
        subconcept="general",
        question_text="¿Cuánto es 5 + 5?",
        options={"A": "10", "B": "9", "C": "11", "D": "12"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="sign_error", explanation="Error de signo."
            ),
            "C": DistractorDetail(
                misconception="table_lookup_error", explanation="Error de tabla."
            ),
            "D": DistractorDetail(
                misconception="left_to_right_precedence",
                explanation="Error de orden.",
            ),
        },
    )
    validator = TaxonomyValidator()
    result = validator.validate_question_taxonomy(
        question, expected_topic="arithmetic", expected_subconcept=None
    )
    assert result.is_valid is True


def test_taxonomy_validator_unknown_custom_topic():
    question = QuizQuestion(
        id="q_custom_topic",
        topic="advanced_calculus",
        subconcept="integrals",
        question_text="¿Cuál es la integral de 2x?",
        options={"A": "x^2", "B": "2", "C": "x", "D": "2x^2"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="differentiated_instead",
                explanation="Derivaste en vez de integrar.",
            ),
            "C": DistractorDetail(
                misconception="missing_power", explanation="Falta potencia."
            ),
            "D": DistractorDetail(
                misconception="forgot_divide_by_power",
                explanation="Olvidaste dividir.",
            ),
        },
    )
    validator = TaxonomyValidator()
    result = validator.validate_question_taxonomy(
        question,
        expected_topic="advanced_calculus",
        expected_subconcept="integrals",
    )
    assert result.is_valid is True
