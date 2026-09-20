"""Database update operation for quiz questions."""

import sqlite3

from core.db.question_mapper import serialize_options_and_distractors
from modes.quiz.contracts.models import QuizQuestion, QuizQuestionCreate

__all__ = ["update_question"]


def update_question(
    conn: sqlite3.Connection,
    question_id: str,
    question: QuizQuestion | QuizQuestionCreate,
    *,
    source: str = "teacher",
    sympy_verified: bool = True,
) -> bool:
    """Replaces a live bank question's content, returning True when updated."""
    options_json, distractors_json = serialize_options_and_distractors(question)
    cursor = conn.execute(
        """
        UPDATE quiz_questions SET
            topic = ?, subconcept = ?, question_text = ?,
            options_json = ?, correct_option = ?, distractors_json = ?,
            sympy_verified = ?, source = ?
        WHERE id = ? AND deleted_at IS NULL
        """,
        (
            question.topic,
            question.subconcept,
            question.question_text,
            options_json,
            question.correct_option,
            distractors_json,
            1 if sympy_verified else 0,
            source,
            question_id,
        ),
    )
    return cursor.rowcount > 0
