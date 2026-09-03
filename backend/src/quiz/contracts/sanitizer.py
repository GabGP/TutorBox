"""Automated sanitization utilities for quiz math text, fractions, and LaTeX delimiters."""

import re
from typing import Any

_LATEX_FRACTION_PATTERN = re.compile(
    r"\\frac\s*\{\s*([^{}]+?)\s*\}\s*\{\s*([^{}]+?)\s*\}"
)
_MATH_DELIMITER_PAIR_PATTERN = re.compile(r"\${1,2}(.*?)\${1,2}", re.DOTALL)
_LATEX_PAREN_DELIMITER_PATTERN = re.compile(r"\\\((.*?)\\\)", re.DOTALL)
_LATEX_BRACKET_DELIMITER_PATTERN = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)


def normalize_latex_fractions(text: str) -> str:
    """Converts LaTeX fraction notation (\\frac{a}{b}) into standard division format (a/b)."""
    if not isinstance(text, str):
        return text
    normalized_text = text
    while _LATEX_FRACTION_PATTERN.search(normalized_text):
        normalized_text = _LATEX_FRACTION_PATTERN.sub(r"\1/\2", normalized_text)
    return normalized_text


def strip_math_delimiters(text: str) -> str:
    """Strips LaTeX math delimiters and normalizes fractions in math text.

    Handles inline math ($...$, \\(...\\)), display math ($$...$$, \\[...\\]),
    and stray delimiter symbols. Ensures question text, equations, and explanations
    are stored as clean plain text for database persistence, mobile web rendering,
    and offline TTS speech.
    """
    if not isinstance(text, str):
        return text
    unwrapped = normalize_latex_fractions(text)
    unwrapped = _LATEX_BRACKET_DELIMITER_PATTERN.sub(r"\1", unwrapped)
    unwrapped = _LATEX_PAREN_DELIMITER_PATTERN.sub(r"\1", unwrapped)
    unwrapped = _MATH_DELIMITER_PAIR_PATTERN.sub(r"\1", unwrapped)
    unwrapped = unwrapped.replace("$", "")
    unwrapped = (
        unwrapped.replace(r"\(", "")
        .replace(r"\)", "")
        .replace(r"\[", "")
        .replace(r"\]", "")
    )
    return unwrapped


def sanitize_option_text(text: str) -> str:
    """Sanitizes an option value by stripping delimiters, fractions, and stray backslashes."""
    if not isinstance(text, str):
        return text
    sanitized = strip_math_delimiters(text)
    sanitized = sanitized.replace("\\", "")
    return sanitized.strip()


def sanitize_options_dict(options: dict[str, Any]) -> dict[str, Any]:
    """Sanitizes all option text values in an options dictionary."""
    return {
        key: sanitize_option_text(value) if isinstance(value, str) else value
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
