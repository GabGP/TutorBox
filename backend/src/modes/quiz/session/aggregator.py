"""Vote aggregation, distribution calculation, and distractor ranking."""

from modes.quiz.session.models import VALID_OPTIONS, RoundTally, StudentVoteRecord


def compute_tally_from_counts(
    counts: dict[str, int], correct_option: str
) -> RoundTally:
    """Computes distribution percentages and accuracy metrics from raw option counts."""
    sanitized_counts: dict[str, int] = {
        option_key: counts.get(option_key, 0) for option_key in VALID_OPTIONS
    }
    total_votes = sum(sanitized_counts.values())

    percentages: dict[str, float] = {
        option_key: (
            round((sanitized_counts[option_key] / total_votes) * 100, 2)
            if total_votes > 0
            else 0.0
        )
        for option_key in VALID_OPTIONS
    }

    correct_count = sanitized_counts.get(correct_option, 0)
    correct_percentage = (
        round((correct_count / total_votes) * 100, 2) if total_votes > 0 else 0.0
    )

    return RoundTally(
        counts=sanitized_counts,
        total_votes=total_votes,
        percentages=percentages,
        correct_option=correct_option,
        correct_count=correct_count,
        correct_percentage=correct_percentage,
    )


def compute_round_tally(
    votes: list[StudentVoteRecord], correct_option: str
) -> RoundTally:
    """Aggregates a list of recorded student votes into a RoundTally."""
    tallies: dict[str, int] = {option_key: 0 for option_key in VALID_OPTIONS}
    for vote in votes:
        if vote.selected_option in tallies:
            tallies[vote.selected_option] += 1

    return compute_tally_from_counts(tallies, correct_option)


def find_top_distractor(
    tally: RoundTally,
) -> tuple[str | None, int, bool]:
    """Identifies the leading distractor and detects ties among distractors.

    Returns:
        (top_distractor_option, top_distractor_count, has_tie)
    """
    distractor_counts = {
        option: tally.counts.get(option, 0)
        for option in VALID_OPTIONS
        if option != tally.correct_option
    }

    max_distractor_votes = max(distractor_counts.values(), default=0)
    if max_distractor_votes == 0:
        return None, 0, False

    leaders = [
        option
        for option, count in distractor_counts.items()
        if count == max_distractor_votes
    ]

    if len(leaders) > 1:
        return None, max_distractor_votes, True

    return leaders[0], max_distractor_votes, False
