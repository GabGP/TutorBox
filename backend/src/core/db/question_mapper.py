"""Row mapper and serialization utilities for quiz questions."""

import json
import sqlite3

from quiz.contracts.models import (
    DistractorDetail,
    QuizQuestion,
    QuizQuestionCreate,
    QuizQuestionResponse,
)


def row_to_quiz_question(row: sqlite3.Row) -> QuizQuestionResponse:
    """Converts a database Row into a validated QuizQuestionResponse."""
    raw_options = json.loads(row["options_json"])
    raw_distractors = json.loads(row["distractors_json"])
    parsed_distractors = {
        key: DistractorDetail(**detail) for key, detail in raw_distractors.items()
    }

    return QuizQuestionResponse(
        id=row["id"],
        topic=row["topic"],
        subconcept=row["subconcept"],
        question_text=row["question_text"],
        options=raw_options,
        correct_option=row["correct_option"],
        distractors=parsed_distractors,
        sympy_verified=bool(row["sympy_verified"]),
        source=row["source"],
        created_at=row["created_at"],
    )


def serialize_options_and_distractors(
    question: QuizQuestion | QuizQuestionCreate,
) -> tuple[str, str]:
    """Serializes options and distractors to JSON strings for database storage."""
    options_serialized = json.dumps(question.options)
    distractors_serialized = json.dumps(
        {key: detail.model_dump() for key, detail in question.distractors.items()}
    )
    return options_serialized, distractors_serialized


def build_quiz_filter_clauses(
    *,
    topic: str | None = None,
    subconcept: str | None = None,
    include_deleted: bool = False,
) -> tuple[str, list[object]]:
    """Builds a SQL WHERE clause and parameter list based on filter criteria."""
    clauses: list[str] = []
    parameters: list[object] = []

    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if topic:
        clauses.append("topic = ?")
        parameters.append(topic)
    if subconcept:
        clauses.append("subconcept = ?")
        parameters.append(subconcept)

    where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_sql, parameters
