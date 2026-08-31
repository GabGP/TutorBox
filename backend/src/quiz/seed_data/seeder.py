"""Database seeder for the default diagnostic quiz question bank."""

import sqlite3

from db.database import get_db_connection
from quiz.contracts.models import QuizQuestion


def seed_question_bank(
    db_or_conn: sqlite3.Connection | str,
    questions: list[QuizQuestion] | None = None,
) -> int:
    """Seeds default verified diagnostic questions into the SQLite database.

    Returns the count of newly inserted questions. Idempotent.
    """
    from db.quiz import create_question, get_question_by_id
    from quiz.seed_data import SEED_QUESTIONS

    target_questions = questions if questions is not None else SEED_QUESTIONS

    if isinstance(db_or_conn, str):
        conn = get_db_connection(db_or_conn)
        should_close = True
    else:
        conn = db_or_conn
        should_close = False

    try:
        inserted_count = 0
        with conn:
            for question in target_questions:
                existing = get_question_by_id(conn, question.id, include_deleted=True)
                if existing is None:
                    create_question(
                        conn,
                        question,
                        source="seed",
                        sympy_verified=True,
                    )
                    inserted_count += 1
        return inserted_count
    finally:
        if should_close:
            conn.close()
