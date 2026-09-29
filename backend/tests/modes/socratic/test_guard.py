"""Output guard: only safe, plain-text Spanish reaches the child (guard.py)."""

import pytest

from modes.socratic.guard import MAX_REPLY_CHARS, check, clean, leaks
from modes.socratic.problems import find_problem

SUM = find_problem("23 + 45")
HINT = "Empieza por las unidades: ¿cuánto es 3 + 5?"


@pytest.mark.parametrize(
    ("raw", "text"),
    [
        ("<think>la suma es 68</think>\n¿Cuánto es 3 + 5?", "¿Cuánto es 3 + 5?"),
        ("razono...</think>¿Qué operación ves?", "¿Qué operación ves?"),
        ("<think>todavía pensando", ""),
        (
            "**Respuesta:** \\(\\frac{1}{2} \\times 4\\) es \\boxed{2}",
            "1/2 × 4 es 2",
        ),
        ("Mensaje reescrito: «¡¡Muy bien!! ¿Sigues??»", "¡Muy bien! ¿Sigues?"),
        ("¡Hola! ¿Cuánto es 3 + 5?", "¿Cuánto es 3 + 5?"),
        ("- Primero suma.\n- Luego resta.", "Primero suma. Luego resta."),
        ("$6 \\div 2$ y $2 \\cdot 3$", "6 ÷ 2 y 2 · 3"),
    ],
)
def test_clean_leaves_plain_text(raw, text):
    assert clean(raw) == text


def test_clean_keeps_at_most_three_short_sentences():
    sentence = "Esta es una oración de práctica bastante larga para el niño."

    text = clean(" ".join([sentence] * 8))

    assert len(text) <= MAX_REPLY_CHARS
    assert text.count(".") == 3


def test_leaks_catches_the_answer_in_digits_or_words():
    assert leaks("La respuesta es 68.", SUM)
    assert leaks("Es sesenta y ocho.", SUM)
    assert not leaks("¿Cuánto es 23 + 45?", SUM)  # the problem itself is fine
    assert leaks("12 ÷ 3 = 4, y ahora 16 ÷ 4", find_problem("16 entre 4"))
    assert leaks("Es 1/2.", find_problem("1/4 + 1/4"))
    assert not leaks("Tres cuartos es 3/4.", find_problem("1/4 + 1/4"))
    assert not leaks("uno", find_problem("1,000,000 + 1"))  # no words for it


def test_a_faithful_rewording_passes():
    text = "¡Empieza por las unidades! ¿Cuánto es 3 + 5?"

    assert check(text, mode="rewrite", source=HINT, problem=SUM) == []


@pytest.mark.parametrize(
    ("text", "issue"),
    [
        ("你好 ¿cuánto es 3 + 5?", "script"),
        ("Let's sumar: ¿cuánto es 3 + 5?", "english"),
        ("¿Cuánto es 3 + 5? Study geometry.", "english"),
        ("Tutor: ¿cuánto es 3 + 5?", "role"),
        ("Pídele que sume: ¿cuánto es 3 + 5?", "role"),
        ("¿Cuánto es \\frac 3 + 5?", "latex"),
        ("¿Cuánto es 3 + 5? " + "Piensa bien. " * 30, "long"),
        ("¿Cuánto es 3 + 5, tonto?", "rude"),
        ("¿Cuánto es 3 + 5? El total es 68.", "leak"),
        ("¿Cuánto es 3 + 5 + 1?", "number"),
        ("¿Cuánto es 3 + 5? Son ocho.", "number"),
        ("¿Cuánto es 3 más cinco?", "lost"),
        ("Suma las unidades 3 y 5.", "no_question"),
        ("Ay, empezons par un deseo: ¿cuánto es 3 + 5?", "drift"),
    ],
)
def test_unsafe_rewordings_are_rejected(text, issue):
    assert issue in check(text, mode="rewrite", source=HINT, problem=SUM)


def test_explanations_must_be_about_math_but_may_use_numbers():
    fraction = "Una fracción es una parte de un todo, como 1/4. ¿Qué parte comes tú?"

    assert check(fraction, mode="explain", source="", problem=None) == []
    assert check(
        "¡Me encanta el fútbol! ¿Y a ti?", mode="explain", source="", problem=None
    ) == ["off_topic"]
    assert check("", mode="explain", source="", problem=None) == ["empty"]
