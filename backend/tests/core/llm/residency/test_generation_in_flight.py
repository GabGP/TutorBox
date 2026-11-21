"""The read-only views of a generation in flight: a countdown alone is not a generation."""

from tests.core.llm.residency.fakes import (
    FakeCountdowns,
    FakeResidencyClient,
    build_fake_manager,
)


def test_no_generation_means_not_in_flight():
    manager = build_fake_manager(FakeResidencyClient(), FakeCountdowns())

    assert manager.quiz_generation_in_flight() is False


def test_a_generation_is_in_flight_only_while_it_runs():
    manager = build_fake_manager(FakeResidencyClient(), FakeCountdowns())

    with manager.generation_in_flight():
        assert manager.quiz_generation_in_flight() is True

    assert manager.quiz_generation_in_flight() is False


def test_an_armed_countdown_does_not_count_as_a_generation():
    manager = build_fake_manager(FakeResidencyClient(), FakeCountdowns())

    manager.load_quiz()

    assert manager.quiz_generation_in_flight() is False
