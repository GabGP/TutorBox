"""ModelResidencyManager mode switches and startup (core/llm/residency/manager.py)."""

import threading
import time

import pytest

from core.llm.residency.manager import ModelResidencyManager
from core.llm.residency.models import ResidencyError, ResidencyUnsupported
from tests.core.llm.residency.fakes import FakeCountdowns, FakeResidencyClient

QUIZ = "qwen2.5:3b"
TUTOR = "hf.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q8_0"


def make_manager(
    client: FakeResidencyClient,
    *,
    enabled: bool = True,
    quiz: str = QUIZ,
    tutor: str = TUTOR,
):
    return ModelResidencyManager(
        client,
        quiz_model=quiz,
        tutor_model=tutor,
        enabled=enabled,
        quiz_idle_seconds=90.0,
        timer_factory=FakeCountdowns(),
    )


@pytest.fixture
def client() -> FakeResidencyClient:
    return FakeResidencyClient()


def test_disabled_manager_never_calls_the_server(client):
    manager = make_manager(client, enabled=False)

    results = [
        manager.apply_mode("tutor"),
        manager.load_quiz(),
        manager.release_quiz(),
        manager.reconcile("quiz"),
    ]
    with manager.generation_in_flight():
        pass

    assert manager.enabled is False
    assert [result.action for result in results] == ["disabled"] * 4
    assert client.calls == []


def test_entering_tutor_mode_loads_the_tutor_model(client):
    manager = make_manager(client)

    result = manager.apply_mode("tutor")

    assert client.calls == [("load", TUTOR)]
    assert result.model == TUTOR
    assert result.action == "loaded"
    assert result.duration_ms == pytest.approx(3200.0)


def test_leaving_tutor_mode_unloads_the_tutor_model(client):
    manager = make_manager(client)
    manager.apply_mode("tutor")

    result = manager.apply_mode("quiz")

    assert client.called() == [("load", TUTOR), ("unload", TUTOR)]
    assert result.action == "unloaded"
    assert result.duration_ms is None


def test_tutor_quiz_apps_sequence_loads_then_unloads(client):
    manager = make_manager(client)

    actions = [
        manager.apply_mode("tutor").action,
        manager.apply_mode("quiz").action,
        manager.apply_mode("apps").action,
    ]

    assert actions == ["loaded", "unloaded", "unloaded"]
    assert client.called() == [("load", TUTOR), ("unload", TUTOR), ("unload", TUTOR)]


def test_a_server_that_is_not_ollama_reports_unsupported(client):
    client.load_error = ResidencyUnsupported("no native API")
    manager = make_manager(client)

    result = manager.apply_mode("tutor")

    assert result.action == "unsupported"
    assert result.detail == "no native API"


def test_a_failed_load_reports_failed_with_the_reason(client):
    client.load_error = ResidencyError("Ollama is unreachable: refused")
    manager = make_manager(client)

    result = manager.apply_mode("tutor")

    assert result.action == "failed"
    assert result.detail == "Ollama is unreachable: refused"


def test_a_failed_unload_reports_failed(client):
    client.unload_error = ResidencyError("HTTP 500")
    manager = make_manager(client)

    assert manager.apply_mode("apps").action == "failed"


def test_same_model_stays_loaded_while_a_quiz_batch_uses_it(client):
    manager = make_manager(client, tutor=QUIZ)
    manager.load_quiz()

    result = manager.apply_mode("apps")

    assert result.action == "kept"
    assert client.called() == [("load", QUIZ)]


def test_same_model_is_unloaded_when_no_quiz_batch_uses_it(client):
    manager = make_manager(client, tutor=QUIZ)

    assert manager.apply_mode("apps").action == "unloaded"


def test_reconcile_unloads_a_leftover_quiz_model_then_applies_the_mode(client):
    client.resident = {QUIZ}
    manager = make_manager(client)

    result = manager.reconcile("tutor")

    assert client.calls == [("resident", None), ("unload", QUIZ), ("load", TUTOR)]
    assert result.action == "loaded"


def test_reconcile_leaves_the_quiz_model_alone_when_it_is_not_resident(client):
    manager = make_manager(client)

    manager.reconcile("quiz")

    assert client.calls == [("resident", None), ("unload", TUTOR)]


def test_reconcile_carries_on_when_the_server_cannot_list_its_models(client):
    client.list_error = ResidencyError("unreachable")
    manager = make_manager(client)

    result = manager.reconcile("tutor")

    assert result.action == "loaded"
    assert client.called() == [("load", TUTOR)]


def test_reconcile_with_one_model_for_both_roles_only_applies_the_mode(client):
    manager = make_manager(client, tutor=QUIZ)

    manager.reconcile("tutor")

    assert client.calls == [("load", QUIZ)]


def test_reconcile_does_nothing_when_disabled(client):
    manager = make_manager(client, enabled=False)

    assert manager.reconcile("tutor").action == "disabled"
    assert client.calls == []


def test_two_quick_switches_end_in_the_state_of_the_last_one(client):
    """The second switch waits for the first to finish loading; its unload comes last."""
    load_started = threading.Event()
    release_load = threading.Event()
    original_load = client.load

    def slow_load(model_name: str) -> float:
        load_started.set()
        release_load.wait(timeout=5)
        return original_load(model_name)

    client.load = slow_load  # type: ignore[method-assign]
    manager = make_manager(client)
    first = threading.Thread(target=manager.apply_mode, args=("tutor",))
    second = threading.Thread(target=manager.apply_mode, args=("quiz",))

    first.start()
    assert load_started.wait(timeout=5)
    second.start()
    time.sleep(0.05)
    assert client.called() == []  # no unload while the tutor load is still running
    release_load.set()
    first.join(timeout=5)
    second.join(timeout=5)

    assert client.called() == [("load", TUTOR), ("unload", TUTOR)]
