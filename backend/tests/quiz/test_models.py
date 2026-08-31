import pytest
from pydantic import ValidationError

from src.quiz.models import (
    DistractorDetail,
    GenerateQuestionRequest,
    MathValidationResult,
    QuestionOptions,
    QuizQuestion,
    QuizQuestionCreate,
    QuizQuestionResponse,
    ValidateQuestionRequest,
)


def sample_distractors() -> dict[str, DistractorDetail]:
    return {
        "B": DistractorDetail(
            misconception="forgot_division",
            explanation="Restaste 4 pero olvidaste dividir entre 2.",
        ),
        "C": DistractorDetail(
            misconception="subtracted_instead_of_divided",
            explanation="Restaste 2 en vez de dividir.",
        ),
        "D": DistractorDetail(
            misconception="divided_before_subtracting",
            explanation="Dividiste antes de restar.",
        ),
    }


def sample_quiz_payload() -> dict:
    return {
        "id": "q_math_001",
        "topic": "pre_algebra",
        "subconcept": "two_step_equations",
        "question_text": "¿Cuál es el valor de x en 2x + 4 = 12?",
        "options": {"A": "4", "B": "8", "C": "3", "D": "6"},
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "forgot_division",
                "explanation": "Restaste 4 pero olvidaste dividir entre 2.",
            },
            "C": {
                "misconception": "subtracted_instead_of_divided",
                "explanation": "Restaste 2 en vez de dividir.",
            },
            "D": {
                "misconception": "divided_before_subtracting",
                "explanation": "Dividiste antes de restar.",
            },
        },
    }


def test_valid_quiz_question_creation():
    payload = sample_quiz_payload()
    question = QuizQuestion.model_validate(payload)
    assert question.id == "q_math_001"
    assert question.correct_option == "A"
    assert len(question.distractors) == 3
    assert "B" in question.distractors
    assert question.options["A"] == "4"


def test_question_options_as_dict():
    opts = QuestionOptions(A="1", B="2", C="3", D="4")
    assert opts.as_dict() == {"A": "1", "B": "2", "C": "3", "D": "4"}


def test_invalid_option_keys_missing_key():
    payload = sample_quiz_payload()
    payload["options"] = {"A": "4", "B": "8", "C": "3"}  # Missing D
    with pytest.raises(ValidationError) as exc:
        QuizQuestion.model_validate(payload)
    assert "Options must contain exactly keys A, B, C, D" in str(exc.value)


def test_empty_option_text_raises_error():
    payload = sample_quiz_payload()
    payload["options"]["A"] = "   "
    with pytest.raises(ValidationError) as exc:
        QuizQuestion.model_validate(payload)
    assert "Option A text cannot be empty" in str(exc.value)


def test_distractor_keys_must_match_non_correct_options():
    payload = sample_quiz_payload()
    # Correct is A, but distractor includes A instead of B
    payload["distractors"] = {
        "A": {
            "misconception": "dummy",
            "explanation": "Explicacion de prueba valida.",
        },
        "C": {
            "misconception": "dummy2",
            "explanation": "Explicacion de prueba valida.",
        },
        "D": {
            "misconception": "dummy3",
            "explanation": "Explicacion de prueba valida.",
        },
    }
    with pytest.raises(ValidationError) as exc:
        QuizQuestion.model_validate(payload)
    assert "Distractors must match non-correct options" in str(exc.value)


def test_distractor_missing_entry():
    payload = sample_quiz_payload()
    del payload["distractors"]["B"]  # Only 2 distractors
    with pytest.raises(ValidationError) as exc:
        QuizQuestion.model_validate(payload)
    assert "Distractors must match non-correct options" in str(exc.value)


def test_quiz_question_create_and_response_models():
    payload = sample_quiz_payload()
    del payload["id"]
    create_req = QuizQuestionCreate.model_validate(payload)
    assert create_req.id is None
    assert create_req.topic == "pre_algebra"

    # Test that QuizQuestionCreate enforces option non-empty validation
    invalid_create = sample_quiz_payload()
    invalid_create["options"]["A"] = "   "
    with pytest.raises(ValidationError):
        QuizQuestionCreate.model_validate(invalid_create)

    res = QuizQuestionResponse(
        **sample_quiz_payload(),
        source="seed",
        sympy_verified=True,
        created_at="2026-08-30T00:00:00Z",
    )
    assert res.source == "seed"
    assert res.sympy_verified is True


def test_generate_and_validate_request_models():
    gen_req = GenerateQuestionRequest(
        topic="arithmetic", subconcept="order_of_operations"
    )
    assert gen_req.topic == "arithmetic"
    assert gen_req.save_to_bank is False

    val_req = ValidateQuestionRequest(
        question=QuizQuestion.model_validate(sample_quiz_payload())
    )
    assert val_req.question.id == "q_math_001"


def test_math_validation_result():
    res = MathValidationResult(is_valid=True, errors=[], details={"calc": "4"})
    assert res.is_valid is True
    assert res.details["calc"] == "4"
