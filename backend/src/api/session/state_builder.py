"""State presentation builder for quiz session API endpoints."""

import sqlite3

from fastapi import HTTPException, status

from api.session.schemas import (
    RoundQuestionView,
    RoundResultView,
    SessionRoundInfo,
    SessionStateResponse,
)
from core.db.question_repository import get_question_by_id
from core.db.round_repository import get_round_by_index
from core.db.session_repository import get_quiz_session
from core.db.vote_repository import count_votes_for_round, get_votes_for_round
from modes.quiz.contracts.models import QuizQuestionResponse
from modes.quiz.session.aggregator import compute_round_tally
from modes.quiz.session.engine import QuizSessionEngine
from modes.quiz.session.evaluator import evaluate_turn_decision
from modes.quiz.session.models import QuizRoundRecord, RoundStatus

__all__ = ["build_session_state"]


def _round_result(
    conn: sqlite3.Connection,
    round_record: QuizRoundRecord,
    question: QuizQuestionResponse,
) -> RoundResultView:
    """Recomputes the reveal outcome read-only, with the same functions /reveal uses."""
    votes = get_votes_for_round(conn, round_record.id)
    tally = compute_round_tally(votes, question.correct_option)
    decision = evaluate_turn_decision(tally, question.distractors)
    return RoundResultView(
        round_id=round_record.id,
        tally=tally,
        decision=decision,
        explanations={
            option: detail.explanation
            for option, detail in question.distractors.items()
        },
    )


def _round_info(
    conn: sqlite3.Connection, round_record: QuizRoundRecord, engine: QuizSessionEngine
) -> SessionRoundInfo:
    """Builds round info; question appears once open, the answer only once revealed."""
    # Timers live in memory, so after a backend restart time_remaining is None
    # (no countdown) rather than 0.0 (expired). Clients must treat None as "no timer".
    info = SessionRoundInfo(
        round_id=round_record.id,
        round_index=round_record.round_index,
        status=round_record.status,
        question_id=round_record.question_id,
        duration_seconds=round_record.duration_seconds,
        time_remaining=engine.get_remaining_time(round_record.id),
        votes_cast=count_votes_for_round(conn, round_record.id),
    )
    if round_record.status == RoundStatus.PENDING.value or not round_record.question_id:
        return info
    question = get_question_by_id(conn, round_record.question_id)
    if question is None:
        return info
    info.question = RoundQuestionView(
        question_text=question.question_text, options=question.options
    )
    if round_record.status == RoundStatus.REVEALED.value:
        info.result = _round_result(conn, round_record, question)
    return info


def build_session_state(
    conn: sqlite3.Connection, session_id: str, engine: QuizSessionEngine
) -> SessionStateResponse:
    """Constructs a SessionStateResponse using public engine queries."""
    session = get_quiz_session(conn, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    current_round = get_round_by_index(conn, session_id, session.current_round_index)
    round_info = _round_info(conn, current_round, engine) if current_round else None

    return SessionStateResponse(
        id=session.id,
        title=session.title,
        topic=session.topic,
        status=session.status,
        current_round_index=session.current_round_index,
        question_count=session.question_count,
        current_round=round_info,
    )
