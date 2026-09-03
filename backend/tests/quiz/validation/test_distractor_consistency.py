import pytest

from quiz.contracts.models import DistractorDetail, QuizQuestion
from quiz.validation.distractor_consistency import (
    DistractorConsistencyValidator,
)


@pytest.fixture
def base_question() -> QuizQuestion:
    return QuizQuestion(
        id="q_dist_test_01",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de x en 5 + x = 12?",
        options={"A": "7", "B": "17", "C": "-7", "D": "5"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Sumaste 5 a 12 obteniendo 17 en vez de restar 5.",
            ),
            "C": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Restaste 12 de 5 dando como resultado -7.",
            ),
            "D": DistractorDetail(
                misconception="forgot_constant",
                explanation="Tomaste el número 5 directamente sin restar de 12.",
            ),
        },
    )


def test_distractor_consistency_valid_question(base_question: QuizQuestion):
    validator = DistractorConsistencyValidator()
    result = validator.validate_distractor_consistency(base_question)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_distractor_consistency_detects_nemotron_contradiction():
    question = QuizQuestion(
        id="q_nemotron_fail",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de b en 12 + b = 9?",
        options={"A": "-3", "B": "3", "C": "0", "D": "2"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Restaste 12 de 9 pero olvidaste el signo negativo, dando 3.",
            ),
            "C": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Si sumas 12 en vez de restar, obtendrías 24, lo cual es incorrecto.",
            ),
            "D": DistractorDetail(
                misconception="applied_op_to_one_side_only",
                explanation="Solo restaste a un lado y dejaste el otro igual.",
            ),
        },
    )
    validator = DistractorConsistencyValidator()
    result = validator.validate_distractor_consistency(question)
    assert result.is_valid is False
    assert any(
        "Distractor 'C' explanation claims result '24', which contradicts option value '0'"
        in err
        for err in result.errors
    )


def test_distractor_consistency_detects_equation_contradiction():
    question = QuizQuestion(
        id="q_eq_fail",
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_text="¿Cuál es el valor de x en 5 + x = 12?",
        options={"A": "7", "B": "0", "C": "17", "D": "5"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="sign_flip_error",
                explanation="Pensaron que restar 5 de ambos lados da x = -5.",
            ),
            "C": DistractorDetail(
                misconception="wrong_inverse_operation",
                explanation="Aplicaron la operación inversa obteniendo 17.",
            ),
            "D": DistractorDetail(
                misconception="applied_op_to_one_side_only",
                explanation="Solo restaron 5 a un lado, pensando que queda x = 0.",
            ),
        },
    )
    validator = DistractorConsistencyValidator()
    result = validator.validate_distractor_consistency(question)
    assert result.is_valid is False
    assert any(
        "Distractor 'B' explanation claims result '-5', which contradicts option value '0'"
        in err
        for err in result.errors
    )
    assert any(
        "Distractor 'D' explanation claims result '0', which contradicts option value '5'"
        in err
        for err in result.errors
    )


def test_distractor_consistency_rejects_too_short_explanation(
    base_question: QuizQuestion,
):
    base_question.distractors["B"].explanation = "Error"
    validator = DistractorConsistencyValidator()
    result = validator.validate_distractor_consistency(base_question)
    assert result.is_valid is False
    assert any("too short" in err for err in result.errors)


def test_distractor_consistency_rejects_claims_of_correct_answer(
    base_question: QuizQuestion,
):
    base_question.distractors[
        "B"
    ].explanation = "Esta es la respuesta correcta para la suma."
    validator = DistractorConsistencyValidator()
    result = validator.validate_distractor_consistency(base_question)
    assert result.is_valid is False
    assert any("incorrectly claims" in err for err in result.errors)


def test_distractor_consistency_fraction_and_decimal_equivalence():
    question = QuizQuestion(
        id="q_frac_dec",
        topic="fractions",
        subconcept="simplification",
        question_text="¿Cuál es la fracción irreducible de 2/4?",
        options={"A": "1/2", "B": "0.5", "C": "2/2", "D": "1/4"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="decimal_conversion",
                explanation="Convertiste la fracción a decimal obteniendo 1/2 en vez de simplificar.",
            ),
            "C": DistractorDetail(
                misconception="incomplete_simplification",
                explanation="Solo simplificaste el denominador dando 2/2.",
            ),
            "D": DistractorDetail(
                misconception="wrong_division",
                explanation="Dividiste entre 4 solo el numerador dando 1/4.",
            ),
        },
    )
    validator = DistractorConsistencyValidator()
    result = validator.validate_distractor_consistency(question)
    assert result.is_valid is True


def test_distractor_consistency_skips_correct_option_key(base_question: QuizQuestion):
    base_question.distractors["A"] = DistractorDetail(
        misconception="dummy",
        explanation="Esta es la opción correcta.",
    )
    validator = DistractorConsistencyValidator()
    result = validator.validate_distractor_consistency(base_question)
    assert result.is_valid is True


def test_distractor_consistency_rejects_boilerplate_response_letter(
    base_question: QuizQuestion,
):
    base_question.distractors[
        "B"
    ].explanation = "Al dividir antes de restar, obtendrías el error de respuesta B."
    validator = DistractorConsistencyValidator()
    result = validator.validate_distractor_consistency(base_question)
    assert result.is_valid is False
    assert any("empty boilerplate" in err for err in result.errors)


def test_distractor_consistency_rejects_boilerplate_option_letter(
    base_question: QuizQuestion,
):
    base_question.distractors[
        "C"
    ].explanation = "Este cálculo lleva al valor de la opción C en la pregunta."
    validator = DistractorConsistencyValidator()
    result = validator.validate_distractor_consistency(base_question)
    assert result.is_valid is False
    assert any("empty boilerplate" in err for err in result.errors)
