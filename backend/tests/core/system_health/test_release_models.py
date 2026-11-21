"""model_release: the quiz model is freed unless a generation runs; the tutor model follows the saved mode."""

import pytest

from core.db.mode_repository import ApplianceMode
from core.llm.residency.manager import ModelResidencyManager
from core.llm.residency.models import ResidencyError, ResidencyUnsupported
from core.system_health.model_release import release_models
from tests.core.llm.residency.fakes import (
    QUIZ_MODEL,
    TUTOR_MODEL,
    FakeCountdowns,
    FakeResidencyClient,
    build_fake_manager,
)


def run(manager: ModelResidencyManager, saved_mode: ApplianceMode | Exception = "quiz"):
    def read_mode() -> ApplianceMode:
        if isinstance(saved_mode, Exception):
            raise saved_mode
        return saved_mode

    return release_models(
        manager, quiz_model_name=QUIZ_MODEL, read_saved_mode=read_mode
    )


def by_kind(actions):
    return {action.kind: action for action in actions}


def test_quiz_mode_unloads_both_models_when_nothing_runs():
    client = FakeResidencyClient()
    manager = build_fake_manager(client)

    actions = by_kind(run(manager, saved_mode="quiz"))

    assert (actions["quiz_model"].target, actions["quiz_model"].action) == (
        QUIZ_MODEL,
        "unloaded",
    )
    assert (actions["tutor_model"].target, actions["tutor_model"].action) == (
        TUTOR_MODEL,
        "unloaded",
    )
    assert ("unload", QUIZ_MODEL) in client.called()
    assert ("unload", TUTOR_MODEL) in client.called()


def test_tutor_mode_frees_the_quiz_model_and_loads_the_tutor_back():
    client = FakeResidencyClient()
    manager = build_fake_manager(client)

    actions = by_kind(run(manager, saved_mode="tutor"))

    assert actions["quiz_model"].action == "unloaded"
    assert actions["tutor_model"].action == "loaded"
    assert ("load", TUTOR_MODEL) in client.called()
    assert ("unload", TUTOR_MODEL) not in client.called()


def test_a_running_generation_keeps_the_quiz_model_loaded():
    client = FakeResidencyClient()
    manager = build_fake_manager(client)

    with manager.generation_in_flight():
        actions = by_kind(run(manager, saved_mode="quiz"))

    assert actions["quiz_model"].action == "kept"
    assert actions["quiz_model"].target == QUIZ_MODEL
    assert actions["quiz_model"].detail == "a question generation is running"
    assert ("unload", QUIZ_MODEL) not in client.called()


def test_an_unreadable_saved_mode_fails_only_the_tutor_step():
    client = FakeResidencyClient()
    manager = build_fake_manager(client)

    actions = by_kind(run(manager, saved_mode=RuntimeError("database locked")))

    assert actions["quiz_model"].action == "unloaded"
    assert actions["tutor_model"].action == "failed"
    assert "database locked" in (actions["tutor_model"].detail or "")


def test_an_ollama_that_is_down_is_reported_not_raised():
    client = FakeResidencyClient()
    client.unload_error = ResidencyError("Ollama is unreachable: refused")
    manager = build_fake_manager(client)

    actions = run(manager, saved_mode="quiz")

    assert [action.action for action in actions] == ["failed", "failed"]
    assert actions[0].detail == "Ollama is unreachable: refused"


def test_a_server_without_the_model_api_is_reported_as_unsupported():
    client = FakeResidencyClient()
    client.unload_error = ResidencyUnsupported("llama.cpp answers 404")
    manager = build_fake_manager(client)

    assert {action.action for action in run(manager, saved_mode="quiz")} == {
        "unsupported"
    }


def test_residency_switched_off_asks_nothing_of_ollama():
    client = FakeResidencyClient()
    manager = ModelResidencyManager(
        client,
        quiz_model=QUIZ_MODEL,
        tutor_model=TUTOR_MODEL,
        enabled=False,
        quiz_idle_seconds=90.0,
        timer_factory=FakeCountdowns(),
    )

    actions = run(manager, saved_mode="tutor")

    assert [action.action for action in actions] == ["disabled", "disabled"]
    assert client.called() == []


@pytest.mark.parametrize("saved_mode", ["quiz", "tutor", "apps"])
def test_every_saved_mode_gives_one_quiz_and_one_tutor_action(saved_mode):
    actions = run(build_fake_manager(FakeResidencyClient()), saved_mode=saved_mode)

    assert [action.kind for action in actions] == ["quiz_model", "tutor_model"]


def test_models_that_are_not_in_memory_are_left_out_of_the_report():
    client = FakeResidencyClient()
    manager = build_fake_manager(client)

    actions = release_models(
        manager,
        quiz_model_name=QUIZ_MODEL,
        read_saved_mode=lambda: "quiz",
        tutor_model_name=TUTOR_MODEL,
        read_resident=lambda: set(),
    )

    # The tutor step still runs (it is harmless), but "unloaded" is not reported for it.
    assert actions == []
    assert ("unload", QUIZ_MODEL) not in client.called()


def test_only_the_resident_quiz_model_is_reported_and_the_tutor_comes_back():
    client = FakeResidencyClient()
    manager = build_fake_manager(client)

    actions = by_kind(
        release_models(
            manager,
            quiz_model_name=QUIZ_MODEL,
            read_saved_mode=lambda: "tutor",
            tutor_model_name=TUTOR_MODEL,
            read_resident=lambda: {QUIZ_MODEL},
        )
    )

    assert actions["quiz_model"].action == "unloaded"
    # Tutor mode loads the tutor model even when it was not in memory: that is reported.
    assert actions["tutor_model"].action == "loaded"
