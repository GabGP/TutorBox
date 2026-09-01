"""Automated sanitization utilities for quiz math text and LaTeX delimiters."""

import re
from typing import Any

_MATH_DELIMITER_PAIR_PATTERN = re.compile(r"\${1,2}(.*?)\${1,2}")


def strip_math_delimiters(text: str) -> str:
    """Strips LaTeX math delimiters ($...$, $$...$$) and stray dollar signs from text.

    Ensures question text, equations, and explanations are stored as clean plain
    text for database persistence, mobile web rendering, and offline TTS speech.
    """
    if not isinstance(text, str):
        return text
    unwrapped = _MATH_DELIMITER_PAIR_PATTERN.sub(r"\1", text)
    return unwrapped.replace("$", "")


def sanitize_options_dict(options: dict[str, Any]) -> dict[str, Any]:
    """Sanitizes all option text values in an options dictionary."""
    return {
        key: strip_math_delimiters(value) if isinstance(value, str) else value
        for key, value in options.items()
    }


def sanitize_distractors_dict(distractors: dict[str, Any]) -> dict[str, Any]:
    """Sanitizes explanations within a distractors dictionary."""
    sanitized: dict[str, Any] = {}
    for key, value in distractors.items():
        if isinstance(value, dict):
            sanitized_detail = dict(value)
            if "explanation" in sanitized_detail and isinstance(
                sanitized_detail["explanation"], str
            ):
                sanitized_detail["explanation"] = strip_math_delimiters(
                    sanitized_detail["explanation"]
                )
            sanitized[key] = sanitized_detail
        else:
            sanitized[key] = value
    return sanitized


def sanitize_quiz_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Sanitizes question_text, options, and distractors in a quiz question dict."""
    sanitized_data = dict(data)
    if "question_text" in sanitized_data and isinstance(
        sanitized_data["question_text"], str
    ):
        sanitized_data["question_text"] = strip_math_delimiters(
            sanitized_data["question_text"]
        )
    if "options" in sanitized_data and isinstance(sanitized_data["options"], dict):
        sanitized_data["options"] = sanitize_options_dict(sanitized_data["options"])
    if "distractors" in sanitized_data and isinstance(
        sanitized_data["distractors"], dict
    ):
        sanitized_data["distractors"] = sanitize_distractors_dict(
            sanitized_data["distractors"]
        )
    return sanitized_data
