"""QuizModelHold (core/llm/residency/quiz_hold.py): in-flight generations and the idle countdown."""

import pytest

from core.llm.residency.quiz_hold import QuizModelHold
from tests.core.llm.residency.fakes import FakeCountdowns


@pytest.fixture
def expired() -> list[str]:
    """Records every idle expiry the hold reports."""
    return []


@pytest.fixture
def hold_and_timers(expired):
    timers = FakeCountdowns()
    hold = QuizModelHold(90.0, lambda: expired.append("idle"), timers)
    return hold, timers


def test_arm_starts_a_daemon_countdown_of_the_idle_length(hold_and_timers):
    hold, timers = hold_and_timers

    hold.arm()

    assert timers.latest.interval == 90.0
    assert timers.latest.daemon is True
    assert timers.latest.started is True
    assert hold.is_held() is True


def test_an_expired_countdown_reports_idle(hold_and_timers, expired):
    hold, timers = hold_and_timers
    hold.arm()

    timers.latest.expire()

    assert expired == ["idle"]
    assert hold.is_held() is False


def test_arm_again_replaces_the_countdown(hold_and_timers, expired):
    hold, timers = hold_and_timers
    hold.arm()
    first = timers.latest

    hold.arm()
    first.expire()  # the replaced countdown fires late: it must not count

    assert first.cancelled is True
    assert expired == []
    assert timers.latest is not first


def test_disarm_cancels_the_countdown(hold_and_timers, expired):
    hold, timers = hold_and_timers
    hold.arm()

    hold.disarm()
    timers.created[0].expire()

    assert timers.created[0].cancelled is True
    assert expired == []
    assert hold.is_held() is False


def test_disarm_without_a_countdown_does_nothing(hold_and_timers):
    hold, timers = hold_and_timers

    hold.disarm()

    assert timers.created == []
    assert hold.is_held() is False


def test_a_generation_holds_the_model_and_blocks_the_countdown(
    hold_and_timers, expired
):
    hold, timers = hold_and_timers
    hold.arm()
    armed = timers.latest
    loads: list[str] = []

    with hold.generation(lambda: loads.append("ensure")):
        assert armed.cancelled is True
        assert hold.is_held() is True
        armed.expire()  # a countdown that already started must not unload mid-generation
        assert expired == []

    assert loads == ["ensure"]


def test_the_countdown_restarts_after_the_last_generation(hold_and_timers, expired):
    hold, timers = hold_and_timers

    with hold.generation(lambda: None):
        pass
    timers.latest.expire()

    assert expired == ["idle"]


def test_overlapping_generations_restart_the_countdown_only_after_the_last(
    hold_and_timers, expired
):
    hold, timers = hold_and_timers

    with hold.generation(lambda: None):
        with hold.generation(lambda: None):
            pass
        assert hold.is_held() is True
        assert expired == []
    timers.latest.expire()

    assert expired == ["idle"]


def test_an_armed_countdown_inside_a_generation_does_not_unload(
    hold_and_timers, expired
):
    hold, timers = hold_and_timers

    with hold.generation(lambda: None):
        hold.arm()
        timers.latest.expire()

    assert expired == []


def test_a_failing_generation_still_releases_its_hold(hold_and_timers, expired):
    hold, timers = hold_and_timers

    with (
        pytest.raises(RuntimeError, match="model crashed"),
        hold.generation(lambda: None),
    ):
        raise RuntimeError("model crashed")

    timers.latest.expire()
    assert expired == ["idle"]
