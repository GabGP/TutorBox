from typing import Any

from quiz.seed_data import SEED_QUESTIONS


def get_canonical_exemplar(topic: str, subconcept: str | None = None) -> dict[str, Any]:
    """Retrieves the matching canonical few-shot exemplar for topic and subconcept from seed bank."""
    for question in SEED_QUESTIONS:
        if question.topic == topic and (
            subconcept is None or question.subconcept == subconcept
        ):
            return question.model_dump(
                exclude={"id", "schema_version"}, exclude_none=True
            )

    for question in SEED_QUESTIONS:
        if question.topic == topic:
            return question.model_dump(
                exclude={"id", "schema_version"}, exclude_none=True
            )

    return {
        "topic": topic,
        "subconcept": subconcept or "general",
        "question_text": f"Pregunta de diagnóstico para {topic}.",
        "options": {
            "A": "Opción correcta",
            "B": "Distractor 1",
            "C": "Distractor 2",
            "D": "Distractor 3",
        },
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "error_conceptual_1",
                "explanation": "Explicación del error conceptual 1.",
            },
            "C": {
                "misconception": "error_conceptual_2",
                "explanation": "Explicación del error conceptual 2.",
            },
            "D": {
                "misconception": "error_conceptual_3",
                "explanation": "Explicación del error conceptual 3.",
            },
        },
    }
