"""Unit tests for similarity helper algorithms used in quiz deduplication."""

from quiz.validation.similarity_helpers import (
    calculate_text_similarity,
    extract_math_core,
    normalize_question_text,
)


def test_normalize_question_text_accents_and_punctuation():
    """Removes accents, punctuation, and converts symbols."""
    raw = "¿Cuál es el valor de: 2 × 3 ÷ 1 + 5?"
    normalized = normalize_question_text(raw)
    assert normalized == "cual es el valor de 2 * 3 / 1 + 5"


def test_normalize_question_text_latex_symbols():
    """Replaces LaTeX multiplication and division macros with standard symbols."""
    latex_text = r"Calcula 4 \cdot 5 \div 2 \times 3"
    normalized = normalize_question_text(latex_text)
    assert normalized == "calcula 4 * 5 / 2 * 3"


def test_extract_math_core_equation():
    """Extracts compact algebraic equation without whitespace or framing."""
    text = "2x + 4 = 10"
    core = extract_math_core(text)
    assert core == "2x+4=10"


def test_extract_math_core_arithmetic():
    """Extracts compact arithmetic expression without framing."""
    text = "Calcula el resultado de 12 + (3 * 4) hoy."
    core = extract_math_core(text)
    assert core == "12+(3*4)"


def test_extract_math_core_none():
    """Returns None when no math expression is present."""
    text = "Solo texto sin numeros ni operadores"
    core = extract_math_core(text)
    assert core is None


def test_calculate_text_similarity_boundaries():
    """Verifies edge cases for string similarity calculation."""
    assert calculate_text_similarity("identico", "identico") == 1.0
    assert calculate_text_similarity("", "") == 1.0

    high_sim = calculate_text_similarity(
        "cual es el resultado de 2 + 3",
        "cual es el resultado de 2 + 4",
    )
    assert 0.70 < high_sim < 1.0

    disjoint_sim = calculate_text_similarity("abc", "xyz")
    assert disjoint_sim == 0.0
