"""Quiz question generation pipeline, prompt engineering, and LLM clients."""

from quiz.generation.generator import GenerationError, QuizQuestionGenerator
from quiz.generation.llm_client import LLMClient, LocalSLMClient, MockLLMClient
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
    "LLMClient",
    "LocalSLMClient",
    "MockLLMClient",
    "QuizQuestionGenerator",
    "build_feedback_prompt",
    "build_quiz_system_prompt",
    "build_quiz_user_prompt",
    "extract_json_dict",
    "process_generated_response",
    "resolve_question_id",
    "shuffle_quiz_question",
]
