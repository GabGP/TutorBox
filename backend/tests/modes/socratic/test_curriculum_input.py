"""CNB topic scope and the text-only input guard (modes/socratic)."""

import pytest

from modes.socratic.curriculum import load_curriculum
from modes.socratic.input_guard import InputProblem, check_input, clean_input
from modes.socratic.text import Folded


def test_curriculum_covers_primaria_grades_1_to_5():
    curriculum = load_curriculum()

    assert {grade for topic in curriculum.topics for grade in topic.grades} == {
        1,
        2,
        3,
        4,
        5,
    }
    assert curriculum.get("fracciones").title == "fracciones"
    assert curriculum.get("calculo") is None


@pytest.mark.parametrize(
    ("message", "topic_id"),
    [
        ("¿Qué es una fracción?", "fracciones"),
        ("¿cómo se lee el reloj?", "tiempo"),
        ("¿cuántos quetzales me dan de vuelto?", "dinero"),
        ("el perímetro del terreno", "perimetro_area"),
        ("la tabla del 7", "multiplicacion"),
        ("números mayas con puntos y barras", "numeracion_maya"),
        ("¿cuál es el sucesor del 99?", "numeracion"),
    ],
)
def test_match_finds_the_cnb_topic(message, topic_id):
    assert load_curriculum().match(Folded.of(message)).id == topic_id


@pytest.mark.parametrize(
    "message",
    [
        "por favor",
        "mi primo vive en el cuarto de al lado",
        "¿cómo funciona?",
        "vamos al restaurante",
    ],
)
def test_everyday_words_are_not_math(message):
    curriculum = load_curriculum()

    assert curriculum.match(Folded.of(message)) is None
    assert not curriculum.mentions_math(Folded.of(message))


def test_later_grades_are_beyond_the_curriculum():
    curriculum = load_curriculum()

    assert curriculum.is_beyond(Folded.of("¿cómo se hace una derivada?"))
    assert curriculum.is_beyond(Folded.of("la raíz cuadrada de 16"))
    assert not curriculum.is_beyond(Folded.of("¿cómo funciona la suma?"))


@pytest.mark.parametrize(
    ("message", "problem"),
    [
        ("   ", InputProblem.EMPTY),
        ("\u200b\u200b", InputProblem.EMPTY),
        ("data:image/png;base64,iVBORw0KGgo", InputProblem.NOT_TEXT),
        ("<img src=x onerror=alert(1)>", InputProblem.NOT_TEXT),
        ("mira ![foto](tarea.jpg)", InputProblem.NOT_TEXT),
        ("https://ejemplo.com/tarea.PNG", InputProblem.NOT_TEXT),
        ("A" * 120, InputProblem.NOT_TEXT),
        ("¿cuánto es " + "1 + " * 80 + "1?", InputProblem.TOO_LONG),
    ],
)
def test_input_that_is_not_a_short_text_question(message, problem):
    assert check_input(message) is problem


def test_plain_math_text_is_accepted():
    assert check_input("¿Es 3 < 5? ¿cuánto es 23 + 45?") is None
    assert clean_input("  23\n+\t45\x00 ") == "23 + 45"
