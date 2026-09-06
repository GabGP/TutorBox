"""Unit tests for the monotonic round voting timer."""

from session.timer import RoundTimer


def test_timer_initial_state():
    timer = RoundTimer(duration_seconds=30)

    assert timer.duration_seconds == 30.0
    assert timer.is_running() is False
    assert timer.is_expired() is False
    assert timer.elapsed_seconds() == 0.0
    assert timer.remaining_seconds() == 0.0


def test_timer_elapsed_and_remaining_with_simulated_clock():
    simulated_now = 100.0
    timer = RoundTimer(duration_seconds=20, clock=lambda: simulated_now)
    timer.start()

    assert timer.is_running() is True
    assert timer.is_expired(current_time=105.0) is False
    assert timer.elapsed_seconds(current_time=105.0) == 5.0
    assert timer.remaining_seconds(current_time=105.0) == 15.0


def test_timer_expiration_and_clamping():
    timer = RoundTimer(duration_seconds=10)
    timer.start(start_time=50.0)

    assert timer.is_expired(current_time=60.0) is True
    assert timer.is_expired(current_time=65.0) is True
    assert timer.remaining_seconds(current_time=65.0) == 0.0
    assert timer.elapsed_seconds(current_time=65.0) == 15.0


def test_timer_stop():
    simulated_now = 10.0
    timer = RoundTimer(duration_seconds=30, clock=lambda: simulated_now)
    timer.start()

    assert timer.is_running() is True
    timer.stop()

    assert timer.is_running() is False
    assert timer.is_expired() is True
    assert timer.remaining_seconds() == 0.0


def test_timer_clamps_minimum_duration():
    timer = RoundTimer(duration_seconds=0)
    assert timer.duration_seconds == 1.0

    negative_timer = RoundTimer(duration_seconds=-10)
    assert negative_timer.duration_seconds == 1.0


def test_timer_default_clock_execution():
    timer = RoundTimer(duration_seconds=5)
    timer.start()

    assert timer.is_running() is True
    assert timer.elapsed_seconds() >= 0.0
    assert timer.remaining_seconds() <= 5.0
    timer.stop()
    assert timer.is_running() is False
