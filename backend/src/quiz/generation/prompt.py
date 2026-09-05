"""Prompt builders and constrained schema formats for SLM quiz question generation."""

from quiz.contracts.taxonomy import CURRICULUM_TAXONOMY
from quiz.generation.protocols import (
    get_derivation_protocol,
    get_structural_recovery_instruction,
)
from quiz.generation.response_format import build_quiz_response_format

__all__ = [
    "build_feedback_prompt",
    "build_quiz_response_format",
    "build_quiz_system_prompt",
    "build_quiz_user_prompt",
]


def build_quiz_system_prompt(
    topic: str | None = None,
    subconcept: str | None = None,
) -> str:
    """Returns the strict system prompt for local SLM question generation."""
    protocol_text = get_derivation_protocol(topic, subconcept)
    return (
        "You are an expert pedagogical math quiz generator for TutorBox (primary school education).\n"
        "Your goal is to generate exactly 1 multiple-choice diagnostic question in strict JSON format.\n"
        f"{protocol_text}\n"
        "MANDATORY SCRATCHPAD USAGE:\n"
        "You MUST execute the cognitive derivation protocol inside the 'derivation_scratchpad' field FIRST.\n"
        "State your chosen root, coefficients, assembled equation, and distractor calculations concisely.\n"
        "Ensure all subsequent fields ('question_text', 'options', 'distractors') strictly match your scratchpad.\n\n"
        "MANDATORY RULES:\n"
        '1. The question must contain exactly 4 options: "A", "B", "C", "D".\n'
        '2. "correct_option" must be one of "A", "B", "C", "D" and mathematically true. '
        "Distribute the correct answer and distinct distractor misconceptions arbitrarily among options A through D.\n"
        '3. "distractors" must be a dictionary with exactly 3 keys for the non-correct options.\n'
        '4. Each distractor MUST include "misconception" (slug) and "explanation" (a friendly Spanish explanation for primary school).\n'
        '5. The "question_text" and distractor "explanation" fields MUST be in Spanish. '
        '"question_text" MUST explicitly formulate the mathematical equation, operation, or problem to solve.\n'
        "6. ANTI-CONTRADICTION RULE: NEVER state a calculated number in an explanation that contradicts the corresponding option value (e.g., never say 'obtendrías 24' if the option is '0').\n"
        "7. Output ONLY the raw JSON object without markdown formatting, preamble, or commentary.\n"
        "8. NOVELTY RULE: You MUST invent a brand-new, unique question with different numerical values, operations, or coefficients.\n"
        "9. Do NOT use LaTeX math delimiters like $x$ or $...$. Write all variables, numbers, and equations as plain text without dollar signs.\n"
        "10. Each value in 'options' must be a concise numerical or algebraic result (e.g. '7', '-3'). NEVER put explanations, sentences, or words like 'correcto' inside options.\n"
        "11. 'question_text' must contain ONLY the question and equation. NEVER append or list options A, B, C, D inside 'question_text'."
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

    return (
        f"Generate 1 diagnostic quiz question for topic '{topic}'"
        + (f" and subconcept '{subconcept}'" if subconcept else "")
        + f".{misconception_guide}"
    )


def build_feedback_prompt(original_prompt: str, errors: list[str]) -> str:
    """Appends validation errors to previous prompt for rejection cycle recovery."""
    error_list = "\n".join(f"- {error_msg}" for error_msg in errors)
    structural_fix = get_structural_recovery_instruction(errors)

    return (
        f"{original_prompt}\n\n"
        "ATTENTION: Your previous response was rejected due to the following errors:\n"
        f"{error_list}\n"
        "CORRECTION INSTRUCTIONS:\n"
        "1. If an option value contradicts its explanation calculation, ensure the option string matches the exact number in the explanation.\n"
        "2. Ensure 'question_text' explicitly includes the full mathematical equation or problem statement.\n"
        f"3. Fix all listed errors and output the valid JSON object strictly.{structural_fix}\n\n"
        "CRITICAL REVISION RULE:\n"
        "If you generate a new problem or equation, recalculate its solution from scratch using backward formulation.\n"
        "DO NOT reuse numbers or computed truth values from the previous rejected attempt.\n"
        "If recalculating, write your revised step-by-step derivation into 'derivation_scratchpad' first."
    )
