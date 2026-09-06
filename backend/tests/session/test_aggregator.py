"""Unit tests for vote aggregation, tally computation, and distractor ranking."""

from session.aggregator import (
    compute_round_tally,
    compute_tally_from_counts,
    find_top_distractor,
)
from session.models import StudentVoteRecord


def test_compute_tally_from_counts_zero_votes():
    tally = compute_tally_from_counts({}, correct_option="A")

    assert tally.total_votes == 0
    assert tally.counts == {"A": 0, "B": 0, "C": 0, "D": 0}
    assert tally.percentages == {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0}
    assert tally.correct_option == "A"
    assert tally.correct_count == 0
    assert tally.correct_percentage == 0.0


def test_compute_tally_from_counts_mixed_votes():
    raw_counts = {"A": 20, "B": 55, "C": 15, "D": 10}
    tally = compute_tally_from_counts(raw_counts, correct_option="A")

    assert tally.total_votes == 100
    assert tally.counts == {"A": 20, "B": 55, "C": 15, "D": 10}
    assert tally.percentages == {"A": 20.0, "B": 55.0, "C": 15.0, "D": 10.0}
    assert tally.correct_count == 20
    assert tally.correct_percentage == 20.0


def test_compute_tally_from_counts_rounds_percentages():
    raw_counts = {"A": 1, "B": 1, "C": 1, "D": 0}
    tally = compute_tally_from_counts(raw_counts, correct_option="B")

    assert tally.total_votes == 3
    assert tally.percentages["A"] == 33.33
    assert tally.percentages["B"] == 33.33
    assert tally.percentages["C"] == 33.33
    assert tally.percentages["D"] == 0.0
    assert tally.correct_count == 1
    assert tally.correct_percentage == 33.33


def test_compute_round_tally_from_vote_records():
    votes = [
        StudentVoteRecord(
            id="v1",
            session_id="s1",
            round_id="r1",
            student_id=1,
            selected_option="A",
            is_correct=True,
        ),
        StudentVoteRecord(
            id="v2",
            session_id="s1",
            round_id="r1",
            student_id=2,
            selected_option="B",
            is_correct=False,
        ),
        StudentVoteRecord(
            id="v3",
            session_id="s1",
            round_id="r1",
            student_id=3,
            selected_option="B",
            is_correct=False,
        ),
        StudentVoteRecord(
            id="v4",
            session_id="s1",
            round_id="r1",
            student_id=4,
            selected_option="C",
            is_correct=False,
        ),
    ]

    tally = compute_round_tally(votes, correct_option="A")

    assert tally.total_votes == 4
    assert tally.counts["A"] == 1
    assert tally.counts["B"] == 2
    assert tally.counts["C"] == 1
    assert tally.counts["D"] == 0
    assert tally.percentages["B"] == 50.0
    assert tally.correct_count == 1
    assert tally.correct_percentage == 25.0


def test_find_top_distractor_when_all_distractors_zero():
    tally = compute_tally_from_counts({"A": 10}, correct_option="A")
    top_distractor, count, has_tie = find_top_distractor(tally)

    assert top_distractor is None
    assert count == 0
    assert has_tie is False


def test_find_top_distractor_single_dominant():
    tally = compute_tally_from_counts(
        {"A": 10, "B": 60, "C": 20, "D": 10}, correct_option="A"
    )
    top_distractor, count, has_tie = find_top_distractor(tally)

    assert top_distractor == "B"
    assert count == 60
    assert has_tie is False


def test_find_top_distractor_tie_between_distractors():
    tally = compute_tally_from_counts(
        {"A": 20, "B": 40, "C": 40, "D": 0}, correct_option="A"
    )
    top_distractor, count, has_tie = find_top_distractor(tally)

    assert top_distractor is None
    assert count == 40
    assert has_tie is True


def test_find_top_distractor_three_way_tie():
    tally = compute_tally_from_counts(
        {"A": 10, "B": 30, "C": 30, "D": 30}, correct_option="A"
    )
    top_distractor, count, has_tie = find_top_distractor(tally)

    assert top_distractor is None
    assert count == 30
    assert has_tie is True
