"""FastAPI dependency providers for Quiz API services."""

from typing import Annotated

from fastapi import Depends

from quiz.generation.generator import QuizQuestionGenerator
from quiz.generation.llm_client import LLMClient, LocalSLMClient
from quiz.validation.validator import MathValidatorInterface, SymPyMathValidator


def get_llm_client() -> LLMClient:
    """Returns the default LLM client for edge inference."""
    return LocalSLMClient()


def get_math_validator() -> MathValidatorInterface:
    """Returns the deterministic SymPy math validator."""
    return SymPyMathValidator()


def get_quiz_generator(
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    validator: Annotated[MathValidatorInterface, Depends(get_math_validator)],
) -> QuizQuestionGenerator:
    """Instantiates the quiz generation pipeline with injected dependencies."""
    return QuizQuestionGenerator(llm_client=llm_client, validator=validator)
