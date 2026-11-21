"""start_residency_reconcile (core/llm/residency/startup.py): the saved mode is applied at boot."""

import logging

import pytest

from core.db.mode_repository import ApplianceMode
from core.llm.residency import factory, startup
from core.llm.residency.manager import ModelResidencyManager
from core.llm.residency.models import ModelResidencyResult
from tests.core.llm.residency.fakes import FakeCountdowns, FakeResidencyClient


class RecordingManager:
    """Stands in for the process manager; remembers the mode it was asked to reconcile."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self.reconciled: list[ApplianceMode] = []
        self.fail = False

    def reconcile(self, mode: ApplianceMode) -> ModelResidencyResult:
        if self.fail:
            raise RuntimeError("database locked")
        self.reconciled.append(mode)
        return ModelResidencyResult(model="tutor", action="loaded")


@pytest.fixture
def saved_mode(monkeypatch: pytest.MonkeyPatch):
    mode: dict[str, ApplianceMode] = {"value": "tutor"}
    monkeypatch.setattr(startup, "get_mode", lambda conn: mode["value"])
    monkeypatch.setattr(startup, "get_db", _fake_database)
    return mode


class _FakeDatabase:
    def __enter__(self):
        return object()

    def __exit__(self, *exc_info):
        return False


def _fake_database(*args, **kwargs):
    return _FakeDatabase()


def test_switched_off_starts_no_thread(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        startup, "get_model_residency", lambda: RecordingManager(enabled=False)
    )

    assert startup.start_residency_reconcile() is None


def test_enabled_reconciles_the_saved_mode_in_a_background_thread(
    monkeypatch, saved_mode
):
    manager = RecordingManager(enabled=True)
    monkeypatch.setattr(startup, "get_model_residency", lambda: manager)

    thread = startup.start_residency_reconcile()
    assert thread is not None
    thread.join(timeout=5)

    assert thread.daemon is True
    assert manager.reconciled == ["tutor"]


def test_a_failure_is_logged_not_raised(monkeypatch, saved_mode, caplog):
    manager = RecordingManager(enabled=True)
    manager.fail = True
    monkeypatch.setattr(startup, "get_model_residency", lambda: manager)
    caplog.set_level(logging.ERROR, logger="core.llm.residency.startup")

    thread = startup.start_residency_reconcile()
    assert thread is not None
    thread.join(timeout=5)

    assert "Startup model residency failed." in caplog.text


def test_the_real_manager_is_used_when_nothing_is_patched(monkeypatch, saved_mode):
    fake_server = FakeResidencyClient()
    monkeypatch.setattr(
        factory,
        "_manager",
        ModelResidencyManager(
            fake_server,
            quiz_model="qwen2.5:3b",
            tutor_model="tutor:latest",
            enabled=True,
            quiz_idle_seconds=90.0,
            timer_factory=FakeCountdowns(),
        ),
    )

    thread = startup.start_residency_reconcile()
    assert thread is not None
    thread.join(timeout=5)

    assert fake_server.calls == [("resident", None), ("load", "tutor:latest")]
