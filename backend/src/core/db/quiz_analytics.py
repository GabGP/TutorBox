"""Mode 1 analytics, read side: per-topic quiz accuracy for a period vs the one before."""

import sqlite3
from dataclasses import dataclass
from datetime import date

from core.db.periods import Period, period_params

__all__ = [
    "TOP_MISCONCEPTIONS",
    "MisconceptionCount",
    "QuizAnalytics",
    "TopicScore",
    "summarize_quiz_analytics",
]

TOP_MISCONCEPTIONS = 5

# A vote's topic is its question's; the session topic covers a hard-deleted question.
_FROM = (
    "FROM quiz_session_votes v "
    "JOIN quiz_sessions s ON s.id = v.session_id "
    "JOIN quiz_session_rounds r ON r.id = v.round_id "
    "LEFT JOIN quiz_questions q ON q.id = r.question_id "
)
_TOPIC = "COALESCE(q.topic, s.topic)"
_IN_PERIOD = "v.created_at >= :start AND v.created_at < :end"


@dataclass(frozen=True)
class TopicScore:
    """How a topic went this period, and the change against the period before."""

    topic: str
    answers: int
    correct: int
    accuracy: float
    previous_accuracy: float | None
    change: float | None


@dataclass(frozen=True)
class MisconceptionCount:
    """A distractor's misconception and how many times students fell for it."""

    misconception: str
    topic: str
    wrong_answers: int


@dataclass(frozen=True)
class QuizAnalytics:
    """The class's quiz answers over one period, best topic first."""

    period: Period
    start: date
    end: date
    students: int
    answers: int
    correct: int
    accuracy: float
    best_topic: str | None
    weakest_topic: str | None
    most_improved_topic: str | None
    topics: list[TopicScore]
    misconceptions: list[MisconceptionCount]


def _percent(correct: int, answers: int) -> float | None:
    return round(100 * correct / answers, 1) if answers else None


def _topic_scores(conn: sqlite3.Connection, params: dict) -> list[TopicScore]:
    rows = conn.execute(
        f"SELECT {_TOPIC}, SUM(v.created_at >= :start), "
        "SUM(v.created_at >= :start AND v.is_correct = 1), "
        "SUM(v.created_at < :start), SUM(v.created_at < :start AND v.is_correct = 1) "
        f"{_FROM} WHERE v.created_at >= :previous AND v.created_at < :end GROUP BY 1",
        params,
    ).fetchall()
    topics = []
    for topic, answers, correct, previous_answers, previous_correct in rows:
        if not answers:
            continue
        accuracy = _percent(correct, answers)
        before = _percent(previous_correct, previous_answers)
        change = None if before is None else round(accuracy - before, 1)
        topics.append(TopicScore(topic, answers, correct, accuracy, before, change))
    topics.sort(key=lambda t: (-t.accuracy, -t.answers, t.topic))
    return topics


def summarize_quiz_analytics(
    conn: sqlite3.Connection, period: Period, day: date
) -> QuizAnalytics:
    """Scores every topic answered in the period that holds day."""
    params = {**period_params(period, day), "limit": TOP_MISCONCEPTIONS}
    topics = _topic_scores(conn, params)
    improved = [t for t in topics if t.change is not None and t.change > 0]
    students = conn.execute(
        f"SELECT COUNT(DISTINCT v.student_id) {_FROM} WHERE {_IN_PERIOD}", params
    ).fetchone()[0]
    misconceptions = conn.execute(
        f"SELECT v.misconception, {_TOPIC}, COUNT(*) AS n {_FROM} "
        f"WHERE {_IN_PERIOD} AND v.is_correct = 0 AND v.misconception IS NOT NULL "
        "GROUP BY 1, 2 ORDER BY n DESC, 1 LIMIT :limit",
        params,
    ).fetchall()
    answers = sum(t.answers for t in topics)
    correct = sum(t.correct for t in topics)
    return QuizAnalytics(
        period=period,
        start=date.fromisoformat(params["start"]),
        end=date.fromisoformat(params["end"]),
        students=students,
        answers=answers,
        correct=correct,
        accuracy=_percent(correct, answers) or 0.0,
        best_topic=topics[0].topic if topics else None,
        weakest_topic=topics[-1].topic if len(topics) > 1 else None,
        most_improved_topic=(
            max(improved, key=lambda t: t.change).topic if improved else None
        ),
        topics=topics,
        misconceptions=[MisconceptionCount(*row) for row in misconceptions],
    )
