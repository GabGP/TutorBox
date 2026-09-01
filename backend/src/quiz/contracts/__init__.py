"""Quiz data models, JSON schemas, and curriculum taxonomy."""

from quiz.contracts.models import (
    DistractorDetail,
    GenerateQuestionRequest,
    MathValidationResult,
    OptionKey,
    QuestionListResponse,
    QuestionOptions,
    QuizDeleteResponse,
    QuizQuestion,
    QuizQuestionBase,
    QuizQuestionCreate,
    QuizQuestionResponse,
    ValidateQuestionRequest,
)
from quiz.contracts.schema import (
    JSON_SCHEMA_DRAFT,
    SCHEMA_ID,
    SCHEMA_VERSION,
    export_quiz_question_schema,
    get_quiz_question_json_schema,
    get_quiz_question_schema_json,
    validate_quiz_question_dict,
)
from quiz.contracts.taxonomy import (
    CURRICULUM_TAXONOMY,
    get_available_topics,
    is_valid_subconcept,
    is_valid_topic,
)

__all__ = [
    "CURRICULUM_TAXONOMY",
    "JSON_SCHEMA_DRAFT",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "DistractorDetail",
    "GenerateQuestionRequest",
    "MathValidationResult",
    "OptionKey",
    "QuestionListResponse",
    "QuestionOptions",
    "QuizDeleteResponse",
    "QuizQuestion",
    "QuizQuestionBase",
    "QuizQuestionCreate",
    "QuizQuestionResponse",
    "ValidateQuestionRequest",
    "export_quiz_question_schema",
    "get_available_topics",
    "get_quiz_question_json_schema",
    "get_quiz_question_schema_json",
    "is_valid_subconcept",
    "is_valid_topic",
    "validate_quiz_question_dict",
]
