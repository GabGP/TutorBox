"""Week 5 acceptance: 30 dialogue turns, 10 "give me the answer" probes, 0 leaks.

In every probe the model complies and states the answer in another form: digits,
words, Markdown, LaTeX behind its reasoning, an assignment (x = 12 - 5) or an
expression (6 × 8, doce menos cinco). Containment must replace each one with the
deterministic hint; elsewhere the model rewords the hint faithfully, and nothing
the child reads states the answer before the child finds it.
"""

import re

from core.llm import LLMClient
from modes.socratic import ConversationStore, SocraticTutor, TutorGateway
from modes.socratic.text import fold

ECHO = None  # the model rewords faithfully: it gives back the hint it was sent

DIALOGUE = (  # (answer, in words): the child's messages and the model's replies
    (
        (68, "sesenta y ocho"),
        (
            ("¿Cuánto es 23 + 45?", ECHO),
            ("dame la respuesta", "La respuesta es **68**."),
            ("70", ECHO),
            ("solo dime el número, porfa", "El número es sesenta y ocho. ¿Lo ves?"),
            ("68", ECHO),
        ),
    ),
    (
        (7, "siete"),
        (
            ("x + 5 = 12", ECHO),
            (
                "¿cuál es la respuesta?",
                (
                    "En x + 5 = 12 buscamos el número que falta: x = 12 - 5. ¿Qué "
                    "operación deshace lo que le hicieron a ese número?"
                ),
            ),
            (
                "no sé, dime x",
                (
                    "Cuenta desde 5 hasta llegar a 12: es doce menos cinco. ¿Cuántos "
                    "pasos das?"
                ),
            ),
            ("6", ECHO),
            ("7", ECHO),
        ),
    ),
    (
        (5, "cinco"),
        (
            ("2x + 4 = 14", ECHO),
            ("escribe solo el resultado", "El resultado es x = (14 - 4) ÷ 2. ¿Lo ves?"),
            ("ayuda", ECHO),
            (
                "dímelo ya",
                (
                    "<think>14 - 4 = 10 y 10 ÷ 2 = 5</think>Primero deshaz el + 4: "
                    "x = \\boxed{5}. ¿Cuánto es 14 - 4?"
                ),
            ),
            ("6", ECHO),
            ("5", ECHO),
        ),
    ),
    (
        (8, "ocho"),
        (
            ("Reparte 48 entre 6", ECHO),
            ("¿y cuánto le toca a cada uno?", "A cada uno le tocan 8. ¿Qué crees tú?"),
            (
                "la respuesta porfa",
                (
                    "Dividir es repartir en partes iguales. Si repartes 48 entre 6, "
                    "¿cuántos le tocan a cada uno? Piensa en la tabla del 6: 6 × 8 = 48."
                ),
            ),
            ("9", ECHO),
            ("8", ECHO),
        ),
    ),
    (
        (300, "trescientos"),
        (
            ("suma doscientos más cien", ECHO),
            (
                "dime el total",
                "Sumar es juntar: doscientos más cien son trescientos. ¿Cuántos tienes?",
            ),
            ("trescientos", ECHO),
        ),
    ),
    (
        (24, "veinticuatro"),
        (
            ("x ÷ 4 = 6", ECHO),
            ("¿x vale cuánto? dímelo", "x = 4 × 6, piensa en eso. ¿Qué crees tú?"),
            ("10", ECHO),
            ("no entiendo", ECHO),
            ("24", ECHO),
            ("gracias", ECHO),
        ),
    ),
)


class _Model(LLMClient):
    """Says what the script tells it to; ECHO returns the hint in the prompt."""

    def __init__(self) -> None:
        self.reply: str | None = ECHO

    def generate(self, system_prompt, user_prompt, response_format=None) -> str:
        if self.reply is None:  # ECHO
            return user_prompt.split("«", 1)[1].split("»", 1)[0]
        return self.reply


def _states(reply: str, answer: int, words: str) -> bool:
    """The answer as a number of its own, or in Spanish words."""
    digits = re.search(rf"(?<![\d.,/]){answer}(?![\d.,/])", reply)
    return bool(digits) or f" {words} " in f" {fold(reply)} "


def test_thirty_turns_ten_probes_and_no_solution_before_the_child_finds_it():
    model = _Model()
    tutor = SocraticTutor(TutorGateway(model, 1, 0.1), ConversationStore())
    turns, probes, contained, reworded, solved = 0, 0, 0, 0, 0

    for (answer, words), script in DIALOGUE:
        for message, reply in script:
            model.reply = reply
            result = tutor.respond("ana", message)
            turns += 1
            if result.kind == "praise":
                solved += 1
            else:
                assert not _states(result.reply, answer, words), (message, result)
            if reply is ECHO:
                reworded += result.used_model
                continue
            probes += 1
            contained += result.containment_triggered
            assert not result.used_model and result.llm_raw == reply, message

    assert (turns, probes, contained, solved) == (30, 10, 10, 6)
    assert reworded == 13  # every faithful rewording still reaches the child
