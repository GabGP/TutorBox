import json
from typing import Any

from quiz.contracts.taxonomy import CURRICULUM_TAXONOMY
from quiz.generation.exemplars import get_canonical_exemplar


def build_quiz_system_prompt() -> str:
    """Returns the strict system prompt for local SLM question generation."""
    return (
        "You are an expert pedagogical math quiz generator for TutorBox (primary school education).\n"
        "Your goal is to generate exactly 1 multiple-choice diagnostic question in strict JSON format.\n"
        "MANDATORY RULES:\n"
        '1. The question must contain exactly 4 options: "A", "B", "C", "D".\n'
        '2. "correct_option" must be one of "A", "B", "C", "D" and mathematically true. '
        "Distribute the correct answer and distinct distractor misconceptions arbitrarily among options A through D.\n"
        '3. "distractors" must be a dictionary with exactly 3 keys for the non-correct options.\n'
        '4. Each distractor MUST include "misconception" (slug) and "explanation" (a friendly Spanish explanation for primary school).\n'
        '5. The "question_text" and distractor "explanation" fields MUST be in Spanish.\n'
        "6. Output ONLY the raw JSON object without markdown formatting, preamble, or commentary.\n"
        "7. NOVELTY RULE: You MUST invent a brand-new, unique question with different numerical values, operations, or coefficients. "
        "NEVER copy or reuse the numbers, equation, or text from the format reference example.\n"
        "8. Do NOT use LaTeX math delimiters like $x$ or $...$. Write all variables, numbers, and equations as plain text without dollar signs."
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

    example_json: dict[str, Any] = get_canonical_exemplar(topic, subconcept)

    return (
        f"Generate 1 diagnostic quiz question for topic '{topic}'"
        + (f" and subconcept '{subconcept}'" if subconcept else "")
        + f".{misconception_guide}\n\n"
        "Required JSON format (schema reference ONLY - do NOT copy these numbers or equation):\n"
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


def build_quiz_response_format() -> dict[str, Any]:
    """Constructs OpenAI-compatible response_format dict for JSON schema constrained decoding."""
    distractor_item = {
        "type": "object",
        "properties": {
            "misconception": {"type": "string"},
            "explanation": {"type": "string"},
        },
        "required": ["misconception", "explanation"],
        "additionalProperties": False,
    }
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "quiz_question",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "subconcept": {"type": "string"},
                    "question_text": {"type": "string"},
                    "options": {
                        "type": "object",
                        "properties": {
                            "A": {"type": "string"},
                            "B": {"type": "string"},
                            "C": {"type": "string"},
                            "D": {"type": "string"},
                        },
                        "required": ["A", "B", "C", "D"],
                        "additionalProperties": False,
                    },
                    "correct_option": {
                        "type": "string",
                        "enum": ["A", "B", "C", "D"],
                    },
                    "distractors": {
                        "type": "object",
                        "properties": {
                            "A": distractor_item,
                            "B": distractor_item,
                            "C": distractor_item,
                            "D": distractor_item,
                        },
                        "additionalProperties": False,
                    },
                },
                "required": [
                    "topic",
                    "subconcept",
                    "question_text",
                    "options",
                    "correct_option",
                    "distractors",
                ],
                "additionalProperties": False,
            },
        },
    }
