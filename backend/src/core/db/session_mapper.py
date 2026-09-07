"""Row mapper utilities for quiz session entities."""

import sqlite3

from modes.quiz.session.models import (
    QuizRoundRecord,
    QuizSessionRecord,
    StudentVoteRecord,
)


def row_to_quiz_session(row: sqlite3.Row) -> QuizSessionRecord:
    """Maps a sqlite3 database row to a validated QuizSessionRecord."""
    return QuizSessionRecord(
        id=row["id"],
        title=row["title"],
        topic=row["topic"],
        teacher_id=row["teacher_id"],
        status=row["status"],
        question_count=row["question_count"],
        current_round_index=row["current_round_index"],
        created_at=str(row["created_at"]) if row["created_at"] else None,
        started_at=str(row["started_at"]) if row["started_at"] else None,
        ended_at=str(row["ended_at"]) if row["ended_at"] else None,
    )


def row_to_quiz_round(row: sqlite3.Row) -> QuizRoundRecord:
    """Maps a sqlite3 database row to a validated QuizRoundRecord."""
    return QuizRoundRecord(
        id=row["id"],
        session_id=row["session_id"],
        question_id=row["question_id"],
        round_index=row["round_index"],
        status=row["status"],
        opened_at=str(row["opened_at"]) if row["opened_at"] else None,
        closed_at=str(row["closed_at"]) if row["closed_at"] else None,
        duration_seconds=row["duration_seconds"],
    )


def row_to_student_vote(row: sqlite3.Row) -> StudentVoteRecord:
    """Maps a sqlite3 database row to a validated StudentVoteRecord."""
    return StudentVoteRecord(
        id=row["id"],
        session_id=row["session_id"],
        round_id=row["round_id"],
        student_id=row["student_id"],
        transport_type=row["transport_type"],
        device_id=row["device_id"],
        selected_option=row["selected_option"],
        is_correct=bool(row["is_correct"]),
        misconception=row["misconception"],
        response_time_ms=row["response_time_ms"],
        created_at=str(row["created_at"]) if row["created_at"] else None,
    )
