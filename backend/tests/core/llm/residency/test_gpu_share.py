"""Where Ollama placed a just-loaded model: all on the GPU, or partly on the (slow) CPU."""

import urllib.request

import pytest

from core.llm.residency.models import ResidencyError
from core.llm.residency.ollama_client import OllamaResidencyClient
from tests.core.llm.residency.fakes import (
    QUIZ_MODEL,
    FakeOllamaHTTP,
    FakeResidencyClient,
    build_fake_manager,
)

ROOT = "http://127.0.0.1:11434"


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> FakeOllamaHTTP:
    fake = FakeOllamaHTTP()
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return fake


def _ps_entry(name: str, size: object, size_vram: object) -> dict[str, object]:
    return {"name": name, "model": name, "size": size, "size_vram": size_vram}


def test_a_model_fully_on_the_gpu_is_100_percent(server):
    server.routes[("GET", "/api/ps")] = {
        "models": [_ps_entry(QUIZ_MODEL, 2_400_000_000, 2_400_000_000)]
    }

    assert OllamaResidencyClient(ROOT, 5).gpu_percent(QUIZ_MODEL) == 100


def test_a_model_partly_on_the_cpu_reports_its_gpu_share(server):
    server.routes[("GET", "/api/ps")] = {
        "models": [
            _ps_entry("other:latest", 1_000, 1_000),
            _ps_entry(QUIZ_MODEL, 2_400_000_000, 1_560_000_000),
        ]
    }

    assert OllamaResidencyClient(ROOT, 5).gpu_percent(QUIZ_MODEL) == 65


@pytest.mark.parametrize(
    "models",
    [
        [],
        [_ps_entry("other:latest", 1_000, 1_000)],
        [_ps_entry(QUIZ_MODEL, 0, 0)],
        [_ps_entry(QUIZ_MODEL, "big", 10)],
    ],
    ids=["nothing-loaded", "another-model", "zero-size", "not-a-number"],
)
def test_no_share_when_ollama_does_not_say(server, models):
    server.routes[("GET", "/api/ps")] = {"models": models}

    assert OllamaResidencyClient(ROOT, 5).gpu_percent(QUIZ_MODEL) is None


def test_a_partial_load_carries_its_share_and_is_logged(caplog):
    client = FakeResidencyClient()
    client.gpu_share = 65

    with caplog.at_level("WARNING"):
        result = build_fake_manager(client).load_quiz()

    assert result.action == "loaded"
    assert result.gpu_percent == 65
    assert "only 65% on the GPU" in caplog.text


def test_an_unreadable_placement_still_reports_the_load():
    client = FakeResidencyClient()
    client.gpu_error = ResidencyError("Ollama is unreachable")

    result = build_fake_manager(client).load_quiz()

    assert result.action == "loaded"
    assert result.gpu_percent is None


def test_a_failed_load_does_not_ask_where_the_model_is():
    client = FakeResidencyClient()
    client.load_error = ResidencyError("Ollama is unreachable")

    result = build_fake_manager(client).load_quiz()

    assert result.action == "failed"
    assert ("gpu", QUIZ_MODEL) not in client.calls
