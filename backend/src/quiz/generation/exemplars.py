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
        "question_text": "¿Cuál es el resultado de 3 + 4 * 2?",
        "options": {"A": "11", "B": "14", "C": "10", "D": "24"},
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "left_to_right_precedence",
                "explanation": "Sumaste 3 + 4 antes de multiplicar por 2.",
            },
            "C": {
                "misconception": "addition_before_multiplication",
                "explanation": "Sumaste antes de resolver la multiplicación prioritaria.",
            },
            "D": {
                "misconception": "ignored_parentheses",
                "explanation": "Ignoraste la jerarquía de las operaciones.",
            },
        },
    }
