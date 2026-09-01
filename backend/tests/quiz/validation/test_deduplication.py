from quiz.contracts.models import DistractorDetail, QuizQuestion
from quiz.validation.deduplication import (
    DeduplicationValidator,
    calculate_text_similarity,
    normalize_question_text,
)


def _build_sample_question(
    question_text: str, question_id: str = "q_test"
) -> QuizQuestion:
    return QuizQuestion(
        id=question_id,
        topic="pre_algebra",
        subconcept="two_step_equations",
        question_text=question_text,
        options={"A": "4", "B": "8", "C": "2", "D": "6"},
        correct_option="A",
        distractors={
            "B": DistractorDetail(
                misconception="forgot_division",
                explanation="Explicación B.",
            ),
            "C": DistractorDetail(
                misconception="divided_before_subtracting",
                explanation="Explicación C.",
            ),
            "D": DistractorDetail(
                misconception="subtracted_instead_of_divided",
                explanation="Explicación D.",
            ),
        },
    )


def test_normalize_question_text():
    raw = "¿Cuál es el valor de x en: 2*x + 4 = 12?"
    normalized = normalize_question_text(raw)
    assert normalized == "cual es el valor de x en 2*x + 4 = 12"

    math_symbols = "10 × 2 ÷ 5 · 3"
    norm_symbols = normalize_question_text(math_symbols)
    assert norm_symbols == "10 * 2 / 5 * 3"


def test_calculate_text_similarity_identical_and_different():
    assert calculate_text_similarity("texto identico", "texto identico") == 1.0
    assert calculate_text_similarity("", "") == 1.0

    sim_high = calculate_text_similarity(
        "cual es el valor de x en 2*x + 4 = 12",
        "cual es el valor de x en 2*x + 4 = 12",
    )
    assert sim_high == 1.0

    sim_disjoint = calculate_text_similarity("abc", "xyz")
    assert sim_disjoint == 0.0

    sim_low = calculate_text_similarity("alpha beta", "gamma delta")
    assert sim_low < 0.60


def test_deduplication_exact_seed_match_fails():
    validator = DeduplicationValidator()
    # Exact duplicate of seed_prealg_two_01
    question = _build_sample_question("¿Cuál es el valor de x en: 2*x + 4 = 12?")
    result = validator.validate_question_novelty(question)

    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "duplicates an existing question in the bank" in result.errors[0]
    assert result.similarity_score == 1.0
    assert result.matched_question_text is not None


def test_deduplication_normalized_variant_fails():
    validator = DeduplicationValidator()
    # Punctuation and case variant of seed_prealg_two_01
    question = _build_sample_question("Cual es el valor de x en 2*x + 4 = 12")
    result = validator.validate_question_novelty(question)

    assert result.is_valid is False
    assert result.similarity_score == 1.0


def test_deduplication_math_symbol_variant_fails():
    validator = DeduplicationValidator()
    # seed_arith_ord_01 is "¿Cuánto es 3 + 4 * 2?"
    question = _build_sample_question("¿Cuánto es 3 + 4 × 2?")
    result = validator.validate_question_novelty(question)

    assert result.is_valid is False
    assert "duplicates an existing question in the bank" in result.errors[0]


def test_deduplication_identical_equation_reordered_fails():
    validator = DeduplicationValidator()
    # Equation 12 = 2*x + 4 is equivalent to 2*x + 4 = 12 in seed bank
    question = _build_sample_question("Calcula x en: 12 = 2*x + 4")
    result = validator.validate_question_novelty(question)

    assert result.is_valid is False
    assert "duplicates an existing question in the bank" in result.errors[0]


def test_deduplication_unique_question_passes():
    validator = DeduplicationValidator()
    # Unique question with different numbers
    unique_question = _build_sample_question("¿Cuál es el valor de x en: 7*x - 5 = 30?")
    result = validator.validate_question_novelty(unique_question)

    assert result.is_valid is True
    assert len(result.errors) == 0


def test_deduplication_custom_reference_questions():
    custom_seed = [
        _build_sample_question("Pregunta conceptual alfa", question_id="custom_1")
    ]
    validator = DeduplicationValidator(
        reference_questions=custom_seed, similarity_threshold=0.85
    )

    duplicate = _build_sample_question("Pregunta conceptual alfa")
    result_dup = validator.validate_question_novelty(duplicate)
    assert result_dup.is_valid is False

    near_dup = _build_sample_question("Pregunta conceptual alfa extra")
    result_near = validator.validate_question_novelty(near_dup)
    assert result_near.is_valid is False

    unique = _build_sample_question("Pregunta completamente diferente")
    result_uniq = validator.validate_question_novelty(unique)
    assert result_uniq.is_valid is True


def test_deduplication_empty_reference_bank_passes():
    validator = DeduplicationValidator(reference_questions=[])
    question = _build_sample_question("Cualquier pregunta")
    result = validator.validate_question_novelty(question)

    assert result.is_valid is True
    assert result.similarity_score == 0.0
    assert result.matched_question_text is None
