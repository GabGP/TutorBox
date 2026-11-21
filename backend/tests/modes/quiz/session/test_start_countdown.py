"""The 3-2-1 before a game's first round: the timer waits, then the full answer time runs."""

from modes.quiz.session.timer import RoundTimer


def test_a_delayed_timer_counts_down_to_its_start():
    timer = RoundTimer(duration_seconds=20, clock=lambda: 100.0)
    timer.start(delay_seconds=3.0)

    assert timer.seconds_until_start(current_time=100.0) == 3.0
    assert timer.seconds_until_start(current_time=101.5) == 1.5
    assert timer.has_started(current_time=102.9) is False
    assert timer.has_started(current_time=103.0) is True
    assert timer.seconds_until_start(current_time=110.0) == 0.0


def test_the_countdown_does_not_eat_into_the_answer_time():
    timer = RoundTimer(duration_seconds=20, clock=lambda: 100.0)
    timer.start(delay_seconds=3.0)

    # During the countdown the round is running with its whole duration left.
    assert timer.is_running(current_time=101.0) is True
    assert timer.remaining_seconds(current_time=101.0) == 20.0
    # Voting time is measured from the end of the countdown.
    assert timer.remaining_seconds(current_time=113.0) == 10.0
    assert timer.is_expired(current_time=123.0) is True


def test_a_negative_delay_starts_at_once():
    timer = RoundTimer(duration_seconds=20, clock=lambda: 100.0)
    timer.start(delay_seconds=-5.0)

    assert timer.has_started(current_time=100.0) is True


def test_an_unstarted_or_stopped_timer_has_no_countdown():
    timer = RoundTimer(duration_seconds=20, clock=lambda: 100.0)
    assert timer.seconds_until_start() == 0.0
    assert timer.has_started() is True

    timer.start(delay_seconds=3.0)
    timer.stop()
    assert timer.seconds_until_start(current_time=100.0) == 0.0
