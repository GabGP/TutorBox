"""Database repository for quiz session vote recording and aggregation."""

import sqlite3

from session.exceptions import VoteAlreadyCastError
from session.models import StudentVoteRecord, TransportType

from db.session_mapper import row_to_student_vote


def record_student_vote(
    conn: sqlite3.Connection,
    vote_id: str,
    session_id: str,
    round_id: str,
    student_id: int,
    selected_option: str,
    *,
    is_correct: bool,
    misconception: str | None = None,
    transport_type: str = TransportType.WEB.value,
    device_id: str | None = None,
    response_time_ms: float | None = None,
) -> StudentVoteRecord:
    """Records an immutable student vote. Raises VoteAlreadyCastError on duplicate."""
    try:
        conn.execute(
            """
            INSERT INTO quiz_session_votes (
                id, session_id, round_id, student_id, transport_type,
                device_id, selected_option, is_correct, misconception,
                response_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vote_id,
                session_id,
                round_id,
                student_id,
                transport_type,
                device_id,
                selected_option,
                1 if is_correct else 0,
                misconception,
                response_time_ms,
            ),
        )
    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed" in str(error):
            raise VoteAlreadyCastError(
                f"Student {student_id} has already voted in round {round_id}.",
                round_id=round_id,
                student_id=student_id,
            ) from error
        raise

    cursor = conn.execute("SELECT * FROM quiz_session_votes WHERE id = ?", (vote_id,))
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError(f"Failed to retrieve recorded vote '{vote_id}'.")
    return row_to_student_vote(row)


def has_student_voted(conn: sqlite3.Connection, round_id: str, student_id: int) -> bool:
    """Checks whether a student has already submitted a vote for a round."""
    cursor = conn.execute(
        "SELECT 1 FROM quiz_session_votes WHERE round_id = ? AND student_id = ?",
        (round_id, student_id),
    )
    return cursor.fetchone() is not None


def get_votes_for_round(
    conn: sqlite3.Connection, round_id: str
) -> list[StudentVoteRecord]:
    """Retrieves all votes cast in a specific round."""
    cursor = conn.execute(
        "SELECT * FROM quiz_session_votes WHERE round_id = ? ORDER BY created_at ASC",
        (round_id,),
    )
    return [row_to_student_vote(row) for row in cursor.fetchall()]


def count_votes_for_round(conn: sqlite3.Connection, round_id: str) -> int:
    """Returns the total number of votes submitted for a given round."""
    cursor = conn.execute(
        "SELECT COUNT(*) FROM quiz_session_votes WHERE round_id = ?",
        (round_id,),
    )
    result = cursor.fetchone()
    return int(result[0]) if result else 0


def get_round_vote_distribution(
    conn: sqlite3.Connection, round_id: str
) -> dict[str, int]:
    """Calculates vote counts for all options ('A', 'B', 'C', 'D') in a round."""
    distribution: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    cursor = conn.execute(
        """
        SELECT selected_option, COUNT(*) as tally
        FROM quiz_session_votes
        WHERE round_id = ?
        GROUP BY selected_option
        """,
        (round_id,),
    )
    for row in cursor.fetchall():
        option = row[0]
        if option in distribution:
            distribution[option] = int(row[1])
    return distribution


def get_votes_for_student(
    conn: sqlite3.Connection, student_id: int
) -> list[StudentVoteRecord]:
    """Retrieves all votes cast by a specific student across all sessions."""
    cursor = conn.execute(
        "SELECT * FROM quiz_session_votes WHERE student_id = ? ORDER BY created_at ASC",
        (student_id,),
    )
    return [row_to_student_vote(row) for row in cursor.fetchall()]
