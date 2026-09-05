"""OpenAI-compatible constrained decoding response format schema for quiz generation."""

from typing import Any

from quiz.contracts.models import VALID_OPTIONS

_SCRATCHPAD_DESCRIPTION = (
    "Mandatory reverse-engineering scratchpad. Briefly execute derivation steps "
    "here in 2-4 lines: 1. Target Root. 2. Coefficients. 3. Equation. 4. Distractors."
)

_QUESTION_TEXT_DESCRIPTION = (
    "Enunciado completo en español con la ecuación o problema a resolver. "
    "NUNCA incluyas opciones A, B, C, D en este texto."
)

_OPTION_DESCRIPTION = (
    "Valor numérico o resultado conciso únicamente (ej. '7', '-3', '5/2'). "
    "NUNCA incluyas explicaciones, oraciones ni palabras como 'correcto'."
)


def build_quiz_response_format() -> dict[str, Any]:
    """Constructs OpenAI-compatible response_format dict for JSON schema constrained decoding."""
    sorted_options = sorted(VALID_OPTIONS)
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
                        "description": _SCRATCHPAD_DESCRIPTION,
                    },
                    "topic": {"type": "string"},
                    "subconcept": {"type": "string"},
                    "question_text": {
                        "type": "string",
                        "description": _QUESTION_TEXT_DESCRIPTION,
                    },
                    "options": {
                        "type": "object",
                        "properties": {
                            key: {"type": "string", "description": _OPTION_DESCRIPTION}
                            for key in sorted_options
                        },
                        "required": sorted_options,
                        "additionalProperties": False,
                    },
                    "correct_option": {
                        "type": "string",
                        "enum": sorted_options,
                    },
                    "distractors": {
                        "type": "object",
                        "properties": {key: distractor_item for key in sorted_options},
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
