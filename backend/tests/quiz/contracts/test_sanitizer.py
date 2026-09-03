"""Unit tests for math delimiter, LaTeX fraction, and option sanitization."""

from src.quiz.contracts.sanitizer import (
    normalize_latex_fractions,
    sanitize_distractors_dict,
    sanitize_option_text,
    sanitize_options_dict,
    sanitize_quiz_dict,
    strip_math_delimiters,
)


def test_strip_math_delimiters_single_dollar():
    assert strip_math_delimiters("$x$") == "x"
    assert strip_math_delimiters("$3x + 5 = 17$") == "3x + 5 = 17"
    raw_text = "¿Cuál es el valor de $x$ en la ecuación: $3x + 5 = 17$?"
    expected = "¿Cuál es el valor de x en la ecuación: 3x + 5 = 17?"
    assert strip_math_delimiters(raw_text) == expected


def test_strip_math_delimiters_double_dollar():
    assert strip_math_delimiters("$$x = 4$$") == "x = 4"
    raw_text = "La respuesta es $$x = 4$$ para la variable $x$."
    expected = "La respuesta es x = 4 para la variable x."
    assert strip_math_delimiters(raw_text) == expected


def test_strip_math_delimiters_latex_parentheses():
    assert strip_math_delimiters(r"\(x\)") == "x"
    assert strip_math_delimiters(r"\(3x + 5 = 17\)") == "3x + 5 = 17"
    raw_text = r"¿Cuál es el valor de \(x\) en la ecuación \(2x + 4 = 12\)?"
    expected = "¿Cuál es el valor de x en la ecuación 2x + 4 = 12?"
    assert strip_math_delimiters(raw_text) == expected


def test_strip_math_delimiters_latex_brackets():
    assert strip_math_delimiters(r"\[x = 4\]") == "x = 4"
    raw_text = r"Evalúa: \[3x + 5 = 17\]"
    expected = "Evalúa: 3x + 5 = 17"
    assert strip_math_delimiters(raw_text) == expected


def test_normalize_latex_fractions():
    assert normalize_latex_fractions(r"\frac{1}{2}") == "1/2"
    assert normalize_latex_fractions(r"\frac{ 3 }{ 4 }") == "3/4"
    assert normalize_latex_fractions(r"\frac{a}{b}") == "a/b"
    assert normalize_latex_fractions(r"\frac{1}{2} + \frac{3}{4}") == "1/2 + 3/4"
    assert normalize_latex_fractions(r"\frac{\frac{1}{2}}{3}") == "1/2/3"
    assert normalize_latex_fractions(42) == 42  # type: ignore[arg-type]


def test_strip_math_delimiters_combined_fractions_and_wrappers():
    assert strip_math_delimiters(r"\(\frac{3}{4}\)") == "3/4"
    assert strip_math_delimiters(r"\[\frac{1}{2}x = 4\]") == "1/2x = 4"
    assert strip_math_delimiters(r"$\frac{5}{8}$") == "5/8"


def test_strip_math_delimiters_stray_and_edge_cases():
    assert strip_math_delimiters("$5") == "5"
    assert strip_math_delimiters("x$") == "x"
    assert strip_math_delimiters("$$$x$$$") == "x"
    assert strip_math_delimiters(r"\(5") == "5"
    assert strip_math_delimiters(r"5\)") == "5"
    assert strip_math_delimiters(r"\[5") == "5"
    assert strip_math_delimiters(r"5\]") == "5"
    assert strip_math_delimiters("Texto plano sin dolares") == "Texto plano sin dolares"
    assert strip_math_delimiters("") == ""


def test_strip_math_delimiters_non_string():
    assert strip_math_delimiters(42) == 42  # type: ignore[arg-type]
    assert strip_math_delimiters(None) is None  # type: ignore[arg-type]


def test_sanitize_option_text():
    assert sanitize_option_text(r"\(4\)") == "4"
    assert sanitize_option_text(r"\4") == "4"
    assert sanitize_option_text(r" \  4  ") == "4"
    assert sanitize_option_text(r"\frac{3}{4}") == "3/4"
    assert sanitize_option_text("4\\") == "4"
    assert sanitize_option_text(99) == 99  # type: ignore[arg-type]


def test_sanitize_options_dict():
    raw_options = {
        "A": r"\($4$\)",
        "B": r"\frac{3}{4}",
        "C": r"\ 8",
        "D": r"\[12\]",
    }
    sanitized = sanitize_options_dict(raw_options)
    assert sanitized == {
        "A": "4",
        "B": "3/4",
        "C": "8",
        "D": "12",
    }


def test_sanitize_options_dict_non_string_values():
    raw_options = {"A": 4, "B": None}
    sanitized = sanitize_options_dict(raw_options)
    assert sanitized == {"A": 4, "B": None}


def test_sanitize_distractors_dict():
    raw_distractors = {
        "B": {
            "misconception": "forgot_division",
            "explanation": r"Restaste \(4\) pero olvidaste dividir entre \(2\).",
        },
        "C": {
            "misconception": "subtracted_instead_of_divided",
            "explanation": r"Restaste \[\frac{1}{2}\] en vez de dividir.",
        },
        "D": "not_a_dict",
    }
    sanitized = sanitize_distractors_dict(raw_distractors)
    assert sanitized["B"]["explanation"] == "Restaste 4 pero olvidaste dividir entre 2."
    assert sanitized["C"]["explanation"] == "Restaste 1/2 en vez de dividir."
    assert sanitized["D"] == "not_a_dict"


def test_sanitize_quiz_dict():
    raw_quiz = {
        "id": "q_test_123",
        "topic": "pre_algebra",
        "subconcept": "two_step_equations",
        "question_text": r"¿Cuál es el valor de \(x\) en \(\frac{1}{2}x + 4 = 12\)?",
        "options": {
            "A": r"\($16$\)",
            "B": r"\frac{8}{2}",
            "C": r"\ 3",
            "D": r"\[6\]",
        },
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "forgot_division",
                "explanation": r"Restaste \(4\) pero olvidaste multiplicar.",
            },
            "C": {
                "misconception": "subtracted_instead_of_divided",
                "explanation": r"Restaste \[\frac{1}{2}\] en vez de multiplicar.",
            },
            "D": {
                "misconception": "divided_before_subtracting",
                "explanation": "Dividiste antes de restar.",
            },
        },
    }
    sanitized = sanitize_quiz_dict(raw_quiz)
    assert sanitized["question_text"] == "¿Cuál es el valor de x en 1/2x + 4 = 12?"
    assert sanitized["options"] == {"A": "16", "B": "8/2", "C": "3", "D": "6"}
    assert (
        sanitized["distractors"]["B"]["explanation"]
        == "Restaste 4 pero olvidaste multiplicar."
    )
    assert (
        sanitized["distractors"]["C"]["explanation"]
        == "Restaste 1/2 en vez de multiplicar."
    )
    assert sanitized["distractors"]["D"]["explanation"] == "Dividiste antes de restar."
