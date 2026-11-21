"""app_probes: the Ollama models and the voice engines, and what happens when either is down."""

import logging
import urllib.error
import urllib.request

import pytest

from core.config import clear_settings_cache, get_settings
from core.llm.residency.models import ResidencyError
from core.llm.residency.ollama_client import OllamaResidencyClient
from core.system_health import app_probes
from core.system_health.app_probes import (
    HEALTH_PROBE_TIMEOUT_SECONDS,
    list_resident_models,
    loaded_voice_engines,
    models_in_memory_from_settings,
    residency_client_from_settings,
)
from tests.core.llm.residency.fakes import FakeOllamaHTTP, FakeResidencyClient

OLLAMA_ROOT = "http://127.0.0.1:11434"


@pytest.fixture
def ollama(monkeypatch: pytest.MonkeyPatch) -> FakeOllamaHTTP:
    fake = FakeOllamaHTTP()
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return fake


@pytest.fixture
def residency(monkeypatch: pytest.MonkeyPatch):
    """Sets SLM_MANAGE_RESIDENCY and the Ollama address for one test, then forgets them."""

    def configure(manage: str) -> None:
        monkeypatch.setenv("SLM_MANAGE_RESIDENCY", manage)
        monkeypatch.setenv("SLM_BASE_URL", OLLAMA_ROOT + "/v1")
        clear_settings_cache()

    yield configure
    clear_settings_cache()


def test_no_client_when_residency_is_off(residency):
    residency("false")

    assert residency_client_from_settings(get_settings()) is None


def test_the_client_talks_to_the_ollama_root_with_the_short_probe_timeout(residency):
    residency("true")

    client = residency_client_from_settings(get_settings())

    assert isinstance(client, OllamaResidencyClient)
    assert HEALTH_PROBE_TIMEOUT_SECONDS == 2.0


def test_residency_off_never_asks_ollama(residency, ollama):
    residency("false")

    assert models_in_memory_from_settings() == []
    assert ollama.requests == []


def test_the_models_in_memory_come_with_their_gpu_share(residency, ollama, monkeypatch):
    residency("true")
    timeouts: list[float | None] = []

    def recording_urlopen(request, timeout=None):
        timeouts.append(timeout)
        return ollama(request, timeout)

    monkeypatch.setattr(urllib.request, "urlopen", recording_urlopen)
    ollama.routes[("GET", "/api/ps")] = {
        "models": [{"name": "qwen2.5:3b", "size": 200, "size_vram": 150}]
    }

    models = models_in_memory_from_settings()

    assert [(model.name, model.gpu_percent) for model in models] == [("qwen2.5:3b", 75)]
    assert timeouts and set(timeouts) == {HEALTH_PROBE_TIMEOUT_SECONDS}


def test_an_ollama_that_is_down_gives_no_models_and_no_error(residency, ollama):
    residency("true")
    ollama.routes[("GET", "/api/ps")] = urllib.error.URLError("connection refused")

    assert models_in_memory_from_settings() == []


def test_the_models_are_listed_by_name_and_a_failed_share_shows_none():
    client = FakeResidencyClient()
    client.resident = {"qwen2.5:3b", "deepseek-r1:1.5b"}
    client.gpu_share = 100

    models = list_resident_models(client)

    assert [(model.name, model.gpu_percent) for model in models] == [
        ("deepseek-r1:1.5b", 100),
        ("qwen2.5:3b", 100),
    ]


def test_a_model_whose_share_cannot_be_read_shows_none():
    client = FakeResidencyClient()
    client.resident = {"qwen2.5:3b"}
    client.gpu_error = ResidencyError("no share")

    assert [
        (model.name, model.gpu_percent) for model in list_resident_models(client)
    ] == [("qwen2.5:3b", None)]


def test_a_failed_model_list_gives_no_models(caplog):
    client = FakeResidencyClient()
    client.list_error = ResidencyError("Ollama is unreachable")

    with caplog.at_level(logging.INFO, logger=app_probes.logger.name):
        assert list_resident_models(client) == []

    assert "Ollama models unavailable" in caplog.text


class FakeTTSRouter:
    def __init__(self, engines: list[str]) -> None:
        self.engines = engines

    def loaded_engines(self) -> list[str]:
        return self.engines


def test_the_loaded_voices_come_from_the_tts_router(monkeypatch):
    monkeypatch.setattr(
        app_probes, "get_tts_router", lambda: FakeTTSRouter(["espeak", "piper"])
    )

    # eSpeak NG holds nothing in memory, so it is not a loaded voice.
    assert loaded_voice_engines() == ["piper"]


def test_a_failing_tts_router_gives_no_voices_and_a_warning(monkeypatch, caplog):
    def broken_router():
        raise RuntimeError("the voice registry is broken")

    monkeypatch.setattr(app_probes, "get_tts_router", broken_router)

    with caplog.at_level(logging.WARNING, logger=app_probes.logger.name):
        assert loaded_voice_engines() == []

    assert "voice engines unavailable" in caplog.text


def test_resident_names_are_unknown_when_residency_is_off(residency):
    residency("false")

    assert app_probes.resident_model_names_from_settings() is None


def test_resident_names_come_from_ollama_and_are_unknown_when_it_is_down(
    residency, ollama
):
    residency("true")
    ollama.routes[("GET", "/api/ps")] = {"models": [{"name": "qwen2.5:3b"}]}
    assert app_probes.resident_model_names_from_settings() == {"qwen2.5:3b"}

    ollama.routes[("GET", "/api/ps")] = OSError("refused")
    assert app_probes.resident_model_names_from_settings() is None
