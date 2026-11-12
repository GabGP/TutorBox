"""One Socratic question per misconception, aimed at the step that went wrong.

The planner names the misconception behind a wrong answer (telemetry/error_type.py)
and asks the question for it here instead of the next rung of the hint ladder.
Every question's only numbers are the problem's own ({p}); it is still re-checked
with the containment check, and None sends the planner back to the ladder.
"""

from modes.socratic.containment import leaks
from modes.socratic.problems import Problem

__all__ = ["QUESTIONS", "misconception_hint"]

QUESTIONS = {
    "alignment_error": "En {p}, escribe un número debajo del otro. ¿Quedaron las "
    "unidades debajo de las unidades?",
    "added_instead_of_subtracted": "Mira bien el signo de {p}. ¿Te pide juntar "
    "o quitar?",
    "borrowing_error": "En {p}, mira las unidades: ¿al número de arriba le alcanza "
    "para quitarle el de abajo, o hay que pedir prestada una decena?",
    "table_lookup_error": "Estuviste muy cerca. Cuenta otra vez los grupos de {p}: "
    "¿te sobró o te faltó algún grupo?",
    "inverted_division": "En {p}, ¿cuál es el número que se reparte y entre cuántos "
    "se reparte? Fíjate en el orden.",
    "ignored_parentheses": "En {p} hay paréntesis. ¿Qué operación se hace antes "
    "que las demás?",
    "left_to_right_precedence": "En {p} hay varias operaciones. ¿Cuál va antes: "
    "la multiplicación y la división, o la suma y la resta?",
    "added_denominators": "En {p}, el denominador dice de qué tamaño son los "
    "pedazos. ¿Se suman los denominadores, o hay que tener pedazos del mismo tamaño?",
    "subtracted_denominators": "En {p}, el denominador dice de qué tamaño son los "
    "pedazos. ¿Se restan los denominadores, o hay que tener pedazos del mismo "
    "tamaño?",
    "wrong_inverse_operation": "En {p}, ¿qué operación le hicieron al número que "
    "falta? ¿Con cuál operación se deshace?",
    "forgot_division": "Vas bien, pero falta un paso. En {p}, el número que falta "
    "está multiplicado: ¿cómo deshaces esa multiplicación?",
    "divided_before_subtracting": "En {p}, ¿qué se deshace antes: lo que se suma "
    "o se resta, o lo que multiplica?",
    "subtracted_instead_of_divided": "En {p}, un número multiplica al que falta. "
    "¿Una multiplicación se deshace restando o dividiendo?",
    "sign_inversion_error": "En {p}, mira el signo del número que acompaña al que "
    "falta. ¿Se deshace sumando o restando?",
    "multiplied_by_percentage_directly": "Un porcentaje es una parte de cada cien. "
    "En {p}, ¿multiplicas por el número completo o por esa parte de cien?",
    "subtracted_percentage_as_raw_number": "En {p}, el porcentaje no es una "
    "cantidad para restar: es una parte del total. ¿Qué parte del total te piden?",
}


def misconception_hint(problem: Problem, slug: str) -> str | None:
    """The question for the misconception; None if it has none or it would leak."""
    template = QUESTIONS.get(slug)
    if template is None:
        return None
    text = template.format(p=problem.text)
    return None if leaks(text, problem) else text
