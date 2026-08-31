import json
from typing import Any

from quiz.taxonomy import CURRICULUM_TAXONOMY


def build_quiz_system_prompt() -> str:
    """Returns the strict system prompt for local SLM question generation."""
    return (
        "You are an expert pedagogical math quiz generator for TutorBox (primary school education).\n"
        "Your goal is to generate exactly 1 multiple-choice diagnostic question in strict JSON format.\n"
        "MANDATORY RULES:\n"
        '1. The question must contain exactly 4 options: "A", "B", "C", "D".\n'
        '2. "correct_option" must be one of "A", "B", "C", "D" and mathematically true.\n'
        '3. "distractors" must be a dictionary with exactly 3 keys for the non-correct options.\n'
        '4. Each distractor MUST include "misconception" (slug) and "explanation" (a friendly Spanish explanation for primary school).\n'
        '5. The "question_text" and distractor "explanation" fields MUST be in Spanish.\n'
        "6. Output ONLY the raw JSON object without markdown formatting, preamble, or commentary."
    )


def build_quiz_user_prompt(
    topic: str,
    subconcept: str | None = None,
    recognized_misconceptions: list[str] | None = None,
) -> str:
    """Constructs the user prompt requesting a question for a given topic/subconcept."""
    misconceptions = recognized_misconceptions
    if not misconceptions and topic in CURRICULUM_TAXONOMY:
        if subconcept and subconcept in CURRICULUM_TAXONOMY[topic]:
            misconceptions = CURRICULUM_TAXONOMY[topic][subconcept]
        else:
            misconceptions = [
                misconception_slug
                for subconcept_misconceptions in CURRICULUM_TAXONOMY[topic].values()
                for misconception_slug in subconcept_misconceptions
            ]

    misconception_guide = (
        f"\nSuggested distractor misconception slugs: {', '.join(misconceptions)}"
        if misconceptions
        else ""
    )

    example_json: dict[str, Any] = {
        "id": "gen_sample_01",
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
                "misconception": "multiplication_error",
                "explanation": "Cometiste un error al multiplicar 4 por 2.",
            },
            "D": {
                "misconception": "multiplied_all",
                "explanation": "Multiplicaste todos los números en vez de seguir la jerarquía.",
            },
        },
    }

    return (
        f"Generate 1 diagnostic quiz question for topic '{topic}'"
        + (f" and subconcept '{subconcept}'" if subconcept else "")
        + f".{misconception_guide}\n\n"
        "Required JSON format:\n"
        f"{json.dumps(example_json, ensure_ascii=False, indent=2)}"
    )


def build_feedback_prompt(original_prompt: str, errors: list[str]) -> str:
    """Appends validation errors to previous prompt for rejection cycle recovery."""
    error_list = "\n".join(f"- {error_msg}" for error_msg in errors)
    return (
        f"{original_prompt}\n\n"
        "ATTENTION: Your previous response was rejected due to the following errors:\n"
        f"{error_list}\n"
        "Please fix all listed errors and output the valid JSON object strictly."
    )
