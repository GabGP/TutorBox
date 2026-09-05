"""OpenAI-compatible constrained decoding response format schema for quiz generation."""

from typing import Any


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
                    "derivation_scratchpad": {
                        "type": "string",
                        "description": (
                            "Mandatory reverse-engineering scratchpad. Briefly execute derivation steps "
                            "here in 2-4 lines: 1. Target Root. 2. Coefficients. 3. Equation. 4. Distractors."
                        ),
                    },
                    "topic": {"type": "string"},
                    "subconcept": {"type": "string"},
                    "question_text": {
                        "type": "string",
                        "description": (
                            "Enunciado completo en español con la ecuación o problema a resolver."
                        ),
                    },
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
                    "derivation_scratchpad",
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
