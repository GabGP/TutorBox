"""OllamaResidencyClient (core/llm/residency/ollama_client.py): the native API calls it makes."""

import urllib.request

import pytest

from core.llm.residency import ollama_client
from core.llm.residency.models import ResidencyUnsupported
from core.llm.residency.ollama_client import OllamaResidencyClient, ollama_server_root
from tests.core.llm.residency.fakes import FakeOllamaHTTP, http_status_error

ROOT = "http://127.0.0.1:11434"
MODEL = "qwen2.5:3b"


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> FakeOllamaHTTP:
    fake = FakeOllamaHTTP()
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return fake


def test_root_drops_the_openai_suffix_and_trailing_slashes():
    assert ollama_server_root("http://127.0.0.1:11434/v1/") == ROOT
    assert ollama_server_root("http://127.0.0.1:8080") == "http://127.0.0.1:8080"


def test_client_root_tolerates_a_trailing_slash(server):
    server.routes[("POST", "/api/generate")] = {"load_duration": 1_000_000}

    OllamaResidencyClient(ROOT + "/", timeout_seconds=5).load(MODEL)

    assert server.requests[0][1] == "/api/generate"


def test_load_keeps_the_model_and_reports_the_server_load_time_in_ms(server):
    server.routes[("POST", "/api/generate")] = {
        "done_reason": "load",
        "load_duration": 3_200_000_000,
    }

    load_ms = OllamaResidencyClient(ROOT, timeout_seconds=5).load(MODEL)

    assert load_ms == pytest.approx(3200.0)
    method, path, body = server.requests[0]
    assert (method, path) == ("POST", "/api/generate")
    assert body == {"model": MODEL, "keep_alive": -1, "stream": False}


def test_load_falls_back_to_the_wall_clock_without_a_server_figure(server, monkeypatch):
    server.routes[("POST", "/api/generate")] = {"done_reason": "load"}
    ticks = iter([10.0, 10.25])
    monkeypatch.setattr(ollama_client.time, "monotonic", lambda: next(ticks))

    load_ms = OllamaResidencyClient(ROOT, timeout_seconds=5).load(MODEL)

    assert load_ms == pytest.approx(250.0)


def test_unload_sends_keep_alive_zero(server):
    server.routes[("POST", "/api/generate")] = {"done_reason": "unload"}

    OllamaResidencyClient(ROOT, timeout_seconds=5).unload(MODEL)

    assert server.requests[0][2] == {"model": MODEL, "keep_alive": 0, "stream": False}


def test_resident_models_lists_names_and_model_fields(server):
    server.routes[("GET", "/api/ps")] = {
        "models": [
            {"name": "qwen2.5:3b", "model": "qwen2.5:3b"},
            {"model": "hf.co/bartowski/x:Q8_0"},
            "not an entry",
            {"size": 1},
        ]
    }

    names = OllamaResidencyClient(ROOT, timeout_seconds=5).resident_models()

    assert names == {"qwen2.5:3b", "hf.co/bartowski/x:Q8_0"}
    assert server.requests[0][:2] == ("GET", "/api/ps")


def test_resident_models_is_empty_when_the_list_is_missing(server):
    server.routes[("GET", "/api/ps")] = {}

    assert OllamaResidencyClient(ROOT, timeout_seconds=5).resident_models() == set()


def test_a_refusal_from_the_server_surfaces_as_unsupported(server):
    server.routes[("GET", "/api/ps")] = http_status_error(404, b"not here")

    with pytest.raises(ResidencyUnsupported):
        OllamaResidencyClient(ROOT, timeout_seconds=5).resident_models()
