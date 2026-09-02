from quiz.contracts.models import QuizQuestion
from quiz.generation.response_processor import (
    extract_json_dict,
    process_generated_response,
    resolve_question_id,
)
from quiz.validation.deduplication import DeduplicationValidator
from quiz.validation.distractor_consistency import DistractorConsistencyValidator
from quiz.validation.taxonomy_validator import TaxonomyValidator
from quiz.validation.validator import SymPyMathValidator


def sample_raw_quiz_dict() -> dict:
    return {
        "id": "q_resp_test_01",
        "topic": "pre_algebra",
        "subconcept": "one_step_equations",
        "question_text": "¿Cuál es el valor de x en 9 + x = 23?",
        "options": {"A": "14", "B": "32", "C": "-14", "D": "9"},
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "wrong_inverse_operation",
                "explanation": "Sumaste 9 a 23 obteniendo 32 en vez de restar 9.",
            },
            "C": {
                "misconception": "sign_flip_error",
                "explanation": "Restaste 23 de 9 dando como resultado -14.",
            },
            "D": {
                "misconception": "applied_op_to_one_side_only",
                "explanation": "Tomaste el número 9 directamente sin restar de 23.",
            },
        },
    }


def test_process_generated_response_valid_all_stages():
    data = sample_raw_quiz_dict()
    question, errors = process_generated_response(
        parsed_json=data,
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_id=None,
        math_validator=SymPyMathValidator(),
        taxonomy_validator=TaxonomyValidator(),
        dedup_validator=DeduplicationValidator(),
        distractor_validator=DistractorConsistencyValidator(),
    )
    assert errors == []
    assert isinstance(question, QuizQuestion)
    assert question.id == "q_resp_test_01"


def test_process_generated_response_fails_distractor_consistency():
    data = sample_raw_quiz_dict()
    # Introduce explicit distractor explanation contradiction
    data["distractors"]["B"]["explanation"] = (
        "Sumaste 12 y 5 obteniendo 24 en vez de restar."
    )
    question, errors = process_generated_response(
        parsed_json=data,
        topic="pre_algebra",
        subconcept="one_step_equations",
        question_id=None,
        math_validator=SymPyMathValidator(),
        taxonomy_validator=TaxonomyValidator(),
        dedup_validator=DeduplicationValidator(),
        distractor_validator=DistractorConsistencyValidator(),
    )
    assert question is None
    assert any("contradicts option value '32'" in err for err in errors)


def test_extract_json_dict_from_markdown_fences():
    raw = '```json\n{"id": "q123", "topic": "arithmetic"}\n```'
    result = extract_json_dict(raw)
    assert result == {"id": "q123", "topic": "arithmetic"}


def test_resolve_question_id():
    assert resolve_question_id({"id": "custom_id"}, None) == "custom_id"
    assert resolve_question_id({}, "explicit_id") == "explicit_id"
    fallback = resolve_question_id({"id": "gen_sample_01"}, None)
    assert fallback.startswith("q_gen_")
