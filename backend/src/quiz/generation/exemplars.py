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
        "question_text": "[Escribe aquí el enunciado completo del problema matemático o ecuación única a resolver]",
        "options": {
            "A": "Valor de la respuesta correcta",
            "B": "Valor del distractor 1",
            "C": "Valor del distractor 2",
            "D": "Valor del distractor 3",
        },
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "nombre_error_conceptual_1",
                "explanation": "Explicación en español del error que lleva al valor de la opción B.",
            },
            "C": {
                "misconception": "nombre_error_conceptual_2",
                "explanation": "Explicación en español del error que lleva al valor de la opción C.",
            },
            "D": {
                "misconception": "nombre_error_conceptual_3",
                "explanation": "Explicación en español del error que lleva al valor de la opción D.",
            },
        },
    }
