"""Provides neutral structural exemplars for LLM prompt formatting without leaking concrete math values."""

from typing import Any


def get_canonical_exemplar(
    topic: str = "algebra_formativa",
    subconcept: str | None = None,
) -> dict[str, Any]:
    """Retrieves a neutral structural few-shot exemplar demonstrating the JSON schema format."""
    subconcept_slug = subconcept or "concepto_general"
    return {
        "topic": topic,
        "subconcept": subconcept_slug,
        "question_text": "¿Cuál es el valor resultante de la expresión de ejemplo?",
        "options": {
            "A": "Respuesta correcta",
            "B": "Distractor por error conceptual 1",
            "C": "Distractor por error conceptual 2",
            "D": "Distractor por error conceptual 3",
        },
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "nombre_del_error_conceptual_1",
                "explanation": "Explicación amigable en español sobre por qué esta opción es incorrecta.",
            },
            "C": {
                "misconception": "nombre_del_error_conceptual_2",
                "explanation": "Explicación amigable en español sobre el segundo tipo de error conceptual.",
            },
            "D": {
                "misconception": "nombre_del_error_conceptual_3",
                "explanation": "Explicación amigable en español sobre el tercer tipo de error conceptual.",
            },
        },
    }
