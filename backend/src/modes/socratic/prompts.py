"""Prompts for the tutor model (DeepSeek-R1-Distill-Qwen-1.5B by default).

Measured on the Jetson: asked to *tutor* freely, the 1.5B distill invents dialogue
turns and states answers; asked to *reword* a hint the backend already chose, it
stays close to it. So the model only rewords hints, or explains a CNB concept,
and guard.py checks every reply either way.
"""

__all__ = ["explain_prompt", "rewrite_prompt"]


def rewrite_prompt(hint: str) -> str:
    """Asks for a friendlier wording of a deterministic hint, nothing more."""
    return (
        "Reescribe este mensaje para un niño de primaria, en español, de forma "
        "amable y en una o dos oraciones cortas. No saludes ni agregues ideas, "
        "resultados, cuentas o números nuevos.\n"
        f"Mensaje: «{hint}»\n"
        "Mensaje reescrito:"
    )


def explain_prompt(question: str, topic_title: str) -> str:
    """Asks for a short, Socratic explanation of a CNB topic."""
    return (
        "Eres un tutor de matemáticas para niños de primaria en Guatemala. "
        "Responde en español, en dos oraciones cortas y sencillas, a la pregunta "
        f"del niño sobre {topic_title}. Explica la idea con un ejemplo pequeño, "
        "sin LaTeX ni negritas, y termina con una pregunta para que el niño "
        "piense.\n"
        f"Pregunta del niño: «{question}»\n"
        "Respuesta:"
    )
