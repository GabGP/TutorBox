"""Deterministic hint ladder and replies (hints.py, replies.py)."""

from fractions import Fraction

import pytest

from modes.socratic import hints
from modes.socratic.curriculum import load_curriculum
from modes.socratic.problems import find_problem
from modes.socratic.replies import (
    GREETING,
    back_to,
    explain_fallback,
    idea_thanks,
    praise,
    social,
    think_first,
    word_problem,
)
from modes.socratic.text import Folded


@pytest.mark.parametrize(
    ("message", "level", "expected"),
    [
        (
            "23 + 45",
            0,
            "¡Vamos a pensarlo juntos! Queremos juntar 23 y 45. ¿Por dónde empiezas?",
        ),
        (
            "23 + 45",
            1,
            (
                "Sumar es juntar. Si tienes 23 y te dan 45 más, ¿cuántos tienes? "
                "Puedes separar cada número en decenas y unidades."
            ),
        ),
        ("23 + 45", 2, "Empieza por las unidades: ¿cuánto es 3 + 5?"),
        ("5 + 3", 2, "Empieza en 5 y cuenta 3 más. ¿A qué número llegas?"),
        (
            "23 + 45",
            3,
            (
                "Mira este ejemplo: 12 + 15 = 27, porque juntamos 12 y 15. "
                "Ahora intenta tú: ¿cuánto es 23 + 45?"
            ),
        ),
        (
            "12 + 15",
            3,
            (
                "Mira este ejemplo: 21 + 14 = 35, porque juntamos 21 y 14. "
                "Ahora intenta tú: ¿cuánto es 12 + 15?"
            ),
        ),
        ("8 - 3", 0, "Vamos a pensar en 8 - 3. ¿Qué pasa cuando a 8 le quitas 3?"),
        (
            "8 - 3",
            1,
            (
                "Restar es quitar. Si tienes 8 y quitas 3, ¿cuántos quedan? "
                "También puedes pensar: ¿qué número sumado a 3 da 8?"
            ),
        ),
        ("8 - 3", 2, "Empieza en 8 y cuenta hacia atrás 3. ¿A qué número llegas?"),
        ("45 - 23", 2, "Empieza por las unidades: ¿cuánto es 5 - 3?"),
        (
            "32 - 25",
            2,
            (
                "Las unidades 2 son menos que 5: pide prestada una decena. "
                "¿Cuánto es 12 - 5?"
            ),
        ),
        (
            "7 por 8",
            0,
            "Vamos a pensar en 7 × 8. ¿Qué significa multiplicar 7 por 8?",
        ),
        (
            "7 por 8",
            1,
            (
                "Multiplicar es sumar el mismo número varias veces: 7 × 8 es sumar "
                "7, 8 veces. ¿Cómo empezarías?"
            ),
        ),
        ("7 por 8", 2, "7 × 8 es 7 × 7 más otro 7. ¿Cuánto es 7 × 7?"),
        (
            "7 por 8",
            3,
            (
                "Mira este ejemplo: 3 × 4 es sumar 3, 4 veces: 3 + 3 + 3 + 3 = 12. "
                "Ahora intenta tú: ¿cuánto es 7 × 8?"
            ),
        ),
        (
            "36 entre 4",
            0,
            "Vamos a pensar en 36 ÷ 4. ¿Qué significa repartir 36 entre 4?",
        ),
        (
            "36 entre 4",
            1,
            (
                "Dividir es repartir en partes iguales. Si repartes 36 entre 4, "
                "¿cuántos le tocan a cada uno? Piensa en la tabla del 4."
            ),
        ),
        (
            "36 entre 4",
            2,
            (
                "¿Qué número multiplicado por 4 da 36? Prueba la tabla del 4: "
                "4 × 1 = 4, 4 × 2 = 8. ¿Sigues?"
            ),
        ),
        (
            "17 entre 5",
            3,
            (
                "Mira este ejemplo: 10 ÷ 2 = 5, porque 2 × 5 = 10. "
                "Ahora intenta tú: ¿cuánto es 17 ÷ 5?"
            ),
        ),
        (
            "1/2 + 1/4",
            1,
            (
                "Mira los denominadores de 1/2 + 1/4: ¿son iguales o diferentes? "
                "Eso te dice cómo empezar."
            ),
        ),
    ],
)
def test_operation_ladders(message, level, expected):
    assert hints.hint(find_problem(message), level) == expected


@pytest.mark.parametrize(
    ("message", "level", "expected"),
    [
        # 16 ÷ 4 = 4: any wording that repeats the 4 would state the answer.
        (
            "16 entre 4",
            0,
            "Vamos a resolver 16 ÷ 4 paso a paso. ¿Qué te pide hacer este problema?",
        ),
        (
            "3 por 1",
            2,
            "Resuelve primero una parte pequeña de 3 × 1. ¿Qué parte puedes hacer tú?",
        ),
        (
            "2x + 4 = 12",
            3,
            (
                "Prueba con números más pequeños que se parezcan a 2x + 4 = 12 y luego "
                "vuelve a tu problema. ¿Qué números usarías?"
            ),
        ),
        (
            "20% de 50",
            1,
            (
                "Un porcentaje es una parte de cada 100. ¿Qué parte de 100 pide "
                "20% de 50, y cómo la buscarías?"
            ),
        ),
    ],
)
def test_generic_hints_when_a_specific_one_is_not_safe(message, level, expected):
    assert hints.hint(find_problem(message), level) == expected


def test_no_safe_example_falls_back_to_the_generic_hint(monkeypatch):
    own_numbers_only = (lambda c, d: c + d, ((23, 45),))
    monkeypatch.setitem(hints._EXAMPLES, "suma", own_numbers_only)

    assert hints.hint(find_problem("23 + 45"), 3).startswith("Prueba con números")


def test_social_replies_only_for_short_messages():
    assert social(Folded.of("¡Hola!")) == GREETING
    assert social(Folded.of("muchas gracias")) == (
        "¡De nada! ¿Quieres practicar otro problema?"
    )
    assert social(Folded.of("adiós")) == "¡Hasta pronto!"
    long_hello = "hola quiero saber cuánto es la suma de muchos números grandes"
    assert social(Folded.of(long_hello)) is None
    assert social(Folded.of("fracciones")) is None


def test_praise_states_the_result_once_found():
    assert praise(find_problem("23 + 45")) == (
        "¡Muy bien! 23 + 45 = 68. ¿Quieres intentar otro problema?"
    )
    assert praise(find_problem("0,5 + 0,25")).startswith(
        "¡Muy bien! 0.5 + 0.25 = 0.75."
    )
    assert praise(find_problem("17 entre 5")).startswith(
        "¡Muy bien! 17 ÷ 5 = 3 y sobran 2."
    )


def test_prompting_replies():
    topic = load_curriculum().get("fracciones")

    assert back_to(find_problem("7 por 8")) == (
        "Sigamos con las matemáticas. ¿Cuánto crees que es 7 × 8?"
    )
    assert "con 5 y 3:" in word_problem([Fraction(5), Fraction(3)])
    assert "fracciones" in think_first(topic)
    assert "fracciones" in explain_fallback(topic)
    assert "un problema de fracciones y" in idea_thanks(topic)
    assert "un problema y" in idea_thanks(None)
