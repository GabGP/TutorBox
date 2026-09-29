"""Deterministic replies: greetings, refusals, praise and prompts to show work.

These never go through the model. They are instant, always Spanish, and each
refusal names what the tutor can do instead, so a child is never left stuck.
"""

from fractions import Fraction

from modes.socratic.curriculum import Topic
from modes.socratic.input_guard import InputProblem
from modes.socratic.numbers import format_value
from modes.socratic.problems import Problem
from modes.socratic.text import Folded

__all__ = [
    "BEYOND",
    "GREETING",
    "INPUT",
    "NEGATIVE",
    "OFF_TOPIC",
    "ORPHAN_ANSWER",
    "SHOW_WORK",
    "back_to",
    "explain_fallback",
    "idea_thanks",
    "praise",
    "social",
    "think_first",
    "word_problem",
]

GREETING = (
    "¡Hola! Soy tu tutor de matemáticas. Escríbeme un problema, por ejemplo "
    "23 + 45, o pregúntame algo como «¿qué es una fracción?». No te doy la "
    "respuesta: te ayudo a encontrarla."
)
OFF_TOPIC = (
    "Solo puedo ayudarte con matemáticas de primaria, como sumas, restas, "
    "fracciones, medidas o geometría. ¿Qué problema quieres practicar?"
)
BEYOND = (
    "Ese tema es de grados más avanzados. Yo te acompaño con las matemáticas "
    "de primero a quinto primaria. ¿Quieres practicar sumas, fracciones, "
    "medidas o geometría?"
)
NEGATIVE = (
    "Ese resultado sería un número negativo, y eso se estudia en grados más "
    "avanzados. En primaria restamos un número pequeño de uno más grande. "
    "¿Quieres intentarlo con otros números?"
)
ORPHAN_ANSWER = (
    "¿De qué problema es ese número? Escríbeme el problema completo, por "
    "ejemplo 23 + 45."
)
SHOW_WORK = (
    "¿Cómo llegaste a ese número? Escríbeme la operación con los números del "
    "problema, usando +, -, × o ÷."
)
INPUT = {
    InputProblem.EMPTY: "Escríbeme tu pregunta de matemáticas.",
    InputProblem.TOO_LONG: (
        "Tu mensaje es muy largo. Escríbeme solo el problema, en pocas palabras."
    ),
    InputProblem.NOT_TEXT: (
        "Solo puedo leer texto, no imágenes ni archivos. Escríbeme el problema "
        "con números y palabras."
    ),
}
_SOCIAL = (
    (("gracias",), "¡De nada! ¿Quieres practicar otro problema?"),
    (("adios", "chao", "bye", "hasta luego", "nos vemos"), "¡Hasta pronto!"),
    (("hola", "buenas", "buenos dias", "saludos", "hey", "que tal"), GREETING),
)


def social(message: Folded) -> str | None:
    """Replies to a short hello, thanks or goodbye; None for anything else."""
    if len(message.tokens) > 6:
        return None
    return next((text for words, text in _SOCIAL if message.has_any(words)), None)


def praise(problem: Problem) -> str:
    """The child found it, so the tutor may now say the whole result."""
    if problem.operation == "division" and problem.target.denominator != 1:
        quotient, rest = divmod(*problem.operands)
        result = f"{quotient} y sobran {rest}"
    else:
        result = format_value(problem.target, problem.decimal)
    return f"¡Muy bien! {problem.text} = {result}. ¿Quieres intentar otro problema?"


def back_to(problem: Problem) -> str:
    return f"Sigamos con las matemáticas. ¿Cuánto crees que es {problem.text}?"


def word_problem(numbers: list[Fraction]) -> str:
    listed = " y ".join(format_value(n) for n in numbers[:4])
    return (
        f"Vamos a pensar en tu problema. ¿Qué operación necesitas hacer con "
        f"{listed}: sumar, restar, multiplicar o dividir? Escríbela con los "
        "números, usando +, -, × o ÷."
    )


def think_first(topic: Topic) -> str:
    return (
        f"¡Buena pregunta sobre {topic.title}! ¿Qué crees tú? Piensa en un "
        "ejemplo y cuéntame tu idea."
    )


def idea_thanks(topic: Topic | None) -> str:
    """After an explanation the child shares an idea the tutor cannot check."""
    subject = f" de {topic.title}" if topic else ""
    return (
        f"¡Gracias por tu idea! Para comprobarla, escríbeme un problema{subject} "
        "y lo resolvemos juntos."
    )


def explain_fallback(topic: Topic) -> str:
    return (
        f"Hablemos de {topic.title}. ¿Qué sabes ya de este tema? Dime un ejemplo "
        "y lo pensamos juntos."
    )
