"""ModelResidencyManager quiz batches and the idle watchdog (core/llm/residency/manager.py)."""

import pytest

from core.llm.residency.manager import ModelResidencyManager
from core.llm.residency.models import ResidencyError
from tests.core.llm.residency.fakes import FakeCountdowns, FakeResidencyClient

QUIZ = "qwen2.5:3b"
TUTOR = "hf.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q8_0"


@pytest.fixture
def client() -> FakeResidencyClient:
    return FakeResidencyClient()


@pytest.fixture
def timers() -> FakeCountdowns:
    return FakeCountdowns()


def make_manager(client, timers, *, tutor: str = TUTOR, enabled: bool = True):
    return ModelResidencyManager(
        client,
        quiz_model=QUIZ,
        tutor_model=tutor,
        enabled=enabled,
        quiz_idle_seconds=90.0,
        timer_factory=timers,
    )


def test_load_quiz_loads_the_quiz_model_and_arms_the_countdown(client, timers):
    manager = make_manager(client, timers)

    result = manager.load_quiz()

    assert client.called() == [("load", QUIZ)]
    assert result.action == "loaded"
    assert result.model == QUIZ
    assert timers.latest.interval == 90.0
    assert timers.latest.started is True


def test_load_quiz_still_arms_the_countdown_when_the_load_fails(client, timers):
    client.load_error = ResidencyError("unreachable")
    manager = make_manager(client, timers)

    result = manager.load_quiz()

    assert result.action == "failed"
    assert timers.latest.started is True


def test_release_quiz_unloads_now_and_stops_the_countdown(client, timers):
    manager = make_manager(client, timers)
    manager.load_quiz()

    result = manager.release_quiz()

    assert client.called() == [("load", QUIZ), ("unload", QUIZ)]
    assert result.action == "unloaded"
    assert timers.latest.cancelled is True


def test_release_quiz_keeps_the_model_the_tutor_is_using(client, timers):
    manager = make_manager(client, timers, tutor=QUIZ)
    manager.apply_mode("tutor")

    result = manager.release_quiz()

    assert result.action == "kept"
    assert client.called() == [("load", QUIZ)]


def test_idle_countdown_unloads_the_quiz_model(client, timers):
    manager = make_manager(client, timers)
    manager.load_quiz()

    timers.latest.expire()

    assert client.called() == [("load", QUIZ), ("unload", QUIZ)]


def test_idle_countdown_keeps_a_shared_model_in_tutor_mode(client, timers):
    manager = make_manager(client, timers, tutor=QUIZ)
    manager.apply_mode("tutor")
    manager.load_quiz()

    timers.latest.expire()

    assert client.called() == [("load", QUIZ), ("load", QUIZ)]  # never unloaded


def test_generation_loads_the_quiz_model_on_demand_and_blocks_the_countdown(
    client, timers
):
    manager = make_manager(client, timers)
    manager.load_quiz()
    armed = timers.latest

    with manager.generation_in_flight():
        assert armed.cancelled is True
        armed.expire()  # the countdown that was running must not unload mid-question
        assert client.called() == [("load", QUIZ), ("load", QUIZ)]  # on-demand load

    assert client.called() == [("load", QUIZ), ("load", QUIZ)]


def test_the_countdown_is_armed_again_after_a_generation(client, timers):
    manager = make_manager(client, timers)

    with manager.generation_in_flight():
        pass
    timers.latest.expire()

    assert client.called() == [("load", QUIZ), ("unload", QUIZ)]


def test_a_countdown_armed_during_a_generation_does_not_unload(client, timers):
    manager = make_manager(client, timers)

    with manager.generation_in_flight():
        manager.load_quiz()
        timers.latest.expire()

    assert client.called() == [("load", QUIZ), ("load", QUIZ)]


def test_a_failed_on_demand_load_does_not_stop_the_generation(client, timers):
    client.load_error = ResidencyError("HTTP 500")
    manager = make_manager(client, timers)
    ran: list[str] = []

    with manager.generation_in_flight():
        ran.append("question")

    assert ran == ["question"]


def test_a_generation_that_raises_still_re_arms_the_countdown(client, timers):
    manager = make_manager(client, timers)

    with pytest.raises(ValueError), manager.generation_in_flight():
        raise ValueError("bad question")

    timers.latest.expire()
    assert client.called() == [("load", QUIZ), ("unload", QUIZ)]


def test_disabled_generation_neither_loads_nor_arms_a_countdown(client, timers):
    manager = make_manager(client, timers, enabled=False)

    with manager.generation_in_flight():
        pass

    assert client.calls == []
    assert timers.created == []
