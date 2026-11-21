"""factory: one process-wide service, built from the database folder and the Ollama settings."""

from pathlib import Path

import pytest

from core.config import clear_settings_cache
from core.system_health import factory
from core.system_health.factory import (
    build_system_health_service,
    get_system_health_service,
)


@pytest.fixture
def fresh_factory(monkeypatch: pytest.MonkeyPatch):
    """Starts with no service built, and leaves none behind for the next test."""
    monkeypatch.setattr(factory, "_service", None)
    yield
    monkeypatch.setattr(factory, "_service", None)


def test_the_service_is_built_once_and_then_shared(fresh_factory):
    first = get_system_health_service()
    second = get_system_health_service()

    assert first is second


def test_the_disk_reading_is_the_partition_of_the_database_folder(
    monkeypatch, tmp_path: Path
):
    database_folder = tmp_path / "data"
    database_folder.mkdir()
    monkeypatch.setenv("DATABASE_PATH", str(database_folder / "utztutor.db"))
    clear_settings_cache()

    snapshot = build_system_health_service().snapshot()

    assert snapshot.disk is not None
    clear_settings_cache()
