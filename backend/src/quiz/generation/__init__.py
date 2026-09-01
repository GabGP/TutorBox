"""Quiz question generation pipeline, prompt engineering, and response validation."""

from quiz.generation.generator import GenerationError, QuizQuestionGenerator
from quiz.generation.prompt import (
    build_feedback_prompt,
    build_quiz_system_prompt,
    build_quiz_user_prompt,
)
from quiz.generation.response_processor import (
    extract_json_dict,
    process_generated_response,
    resolve_question_id,
)
from quiz.generation.shuffler import shuffle_quiz_question

__all__ = [
    "GenerationError",
    "QuizQuestionGenerator",
    "build_feedback_prompt",
    "build_quiz_system_prompt",
    "build_quiz_user_prompt",
    "extract_json_dict",
    "process_generated_response",
    "resolve_question_id",
    "shuffle_quiz_question",
]
