"""Database repository for quiz questions."""

import sqlite3
import uuid

from db.quiz_mapper import (
    build_quiz_filter_clauses,
    row_to_quiz_question,
    serialize_options_and_distractors,
)
from quiz.contracts.models import (
    QuizQuestion,
    QuizQuestionCreate,
    QuizQuestionResponse,
)

DEFAULT_QUESTION_LIMIT: int = 50
DEFAULT_RANDOM_QUESTIONS_COUNT: int = 5


def create_question(
    conn: sqlite3.Connection,
    question: QuizQuestion | QuizQuestionCreate,
    *,
    source: str = "llm",
    sympy_verified: bool = False,
) -> str:
    """Inserts a quiz question into the question bank and returns its unique ID."""
    question_identifier = getattr(question, "id", None) or f"q_{uuid.uuid4().hex[:12]}"
    options_json, distractors_json = serialize_options_and_distractors(question)

    conn.execute(
        """
        INSERT INTO quiz_questions (
            id, topic, subconcept, question_text,
            options_json, correct_option, distractors_json,
            sympy_verified, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            question_identifier,
            question.topic,
            question.subconcept,
            question.question_text,
            options_json,
            question.correct_option,
            distractors_json,
            1 if sympy_verified else 0,
            source,
        ),
    )
    return question_identifier


def get_question_by_id(
    conn: sqlite3.Connection,
    question_id: str,
    *,
    include_deleted: bool = False,
) -> QuizQuestionResponse | None:
    """Retrieves a quiz question by ID."""
    query = "SELECT * FROM quiz_questions WHERE id = ?"
    if not include_deleted:
        query += " AND deleted_at IS NULL"

    cursor = conn.execute(query, (question_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return row_to_quiz_question(row)


def list_questions(
    conn: sqlite3.Connection,
    *,
    topic: str | None = None,
    subconcept: str | None = None,
    limit: int = DEFAULT_QUESTION_LIMIT,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[QuizQuestionResponse]:
    """Lists quiz questions with filtering and pagination."""
    where_sql, params = build_quiz_filter_clauses(
        topic=topic, subconcept=subconcept, include_deleted=include_deleted
    )
    full_query = (
        f"SELECT * FROM quiz_questions{where_sql} "
        f"ORDER BY created_at DESC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    cursor = conn.execute(full_query, params)
    return [row_to_quiz_question(row) for row in cursor.fetchall()]


def get_random_questions(
    conn: sqlite3.Connection,
    *,
    topic: str | None = None,
    subconcept: str | None = None,
    count: int = DEFAULT_RANDOM_QUESTIONS_COUNT,
) -> list[QuizQuestionResponse]:
    """Samples random quiz questions for session generation."""
    where_sql, params = build_quiz_filter_clauses(
        topic=topic, subconcept=subconcept, include_deleted=False
    )
    full_query = f"SELECT * FROM quiz_questions{where_sql} ORDER BY RANDOM() LIMIT ?"
    params.append(count)

    cursor = conn.execute(full_query, params)
    return [row_to_quiz_question(row) for row in cursor.fetchall()]


def count_questions(
    conn: sqlite3.Connection,
    *,
    topic: str | None = None,
    subconcept: str | None = None,
    include_deleted: bool = False,
) -> int:
    """Returns the count of questions matching criteria."""
    where_sql, params = build_quiz_filter_clauses(
        topic=topic, subconcept=subconcept, include_deleted=include_deleted
    )
    full_query = f"SELECT COUNT(*) FROM quiz_questions{where_sql}"

    cursor = conn.execute(full_query, params)
    result = cursor.fetchone()
    return int(result[0]) if result else 0


def soft_delete_question(conn: sqlite3.Connection, question_id: str) -> bool:
    """Soft deletes a question by setting deleted_at timestamp."""
    cursor = conn.execute(
        "UPDATE quiz_questions SET deleted_at = CURRENT_TIMESTAMP "
        "WHERE id = ? AND deleted_at IS NULL",
        (question_id,),
    )
    return cursor.rowcount > 0
