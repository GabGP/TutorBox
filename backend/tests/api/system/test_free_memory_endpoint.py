"""POST /api/v1/system/free-memory: staff only; reports what each step did and never fails on Ollama."""

import time
import urllib.error
import urllib.request
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from core.llm.residency.manager import ModelResidencyManager
from core.llm.residency.ollama_client import OllamaResidencyClient
from core.system_health import factory
from core.system_health.factory import get_memory_releaser
from core.system_health.memory_release import MemoryReleaser, ReleasePhase
from core.system_health.release_report import ReleaseAction
from src.main import app
from tests.core.llm.residency.fakes import FakeOllamaHTTP

RELEASE_URL = "/api/v1/system/free-memory"
QUIZ_MODEL = "qwen2.5:3b"
TUTOR_MODEL = "tutor-model:1.5b"


@pytest.fixture
def no_settle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)


@pytest.fixture
def fake_releaser() -> Iterator[list[ReleaseAction]]:
    """Replaces the release with one phase that reports a single voice unloaded."""
    actions = [ReleaseAction(target="voz piper", kind="voice", action="unloaded")]
    releaser = MemoryReleaser(
        phases=[ReleasePhase("voces", "voice", lambda: actions)],
        read_available_mb=lambda: 1000.0,
        invalidate_snapshot=lambda: None,
        settle_seconds=0.0,
    )
    app.dependency_overrides[get_memory_releaser] = lambda: releaser
    yield actions
    app.dependency_overrides.pop(get_memory_releaser, None)


def test_the_release_needs_a_session(staff_db, client: TestClient):
    assert client.post(RELEASE_URL).status_code == 401


def test_a_student_cannot_release_memory(
    staff_db, client: TestClient, student_headers, fake_releaser
):
    response = client.post(RELEASE_URL, headers=student_headers)

    assert response.status_code == 403


def test_a_teacher_gets_the_report(
    staff_db, client: TestClient, teacher_headers, fake_releaser
):
    response = client.post(RELEASE_URL, headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["available_before_mb"] == 1000.0
    assert body["available_after_mb"] == 1000.0
    assert body["freed_mb"] == 0.0
    assert body["actions"] == [
        {"target": "voz piper", "kind": "voice", "action": "unloaded", "detail": None}
    ]


def test_with_ollama_down_both_models_fail_and_nothing_raises(
    staff_db,
    client: TestClient,
    teacher_headers,
    no_settle,
    monkeypatch: pytest.MonkeyPatch,
):
    ollama = FakeOllamaHTTP()
    refused = urllib.error.URLError("connection refused")
    ollama.routes[("POST", "/api/generate")] = refused
    ollama.routes[("GET", "/api/ps")] = refused
    monkeypatch.setattr(urllib.request, "urlopen", ollama)
    manager = ModelResidencyManager(
        OllamaResidencyClient("http://127.0.0.1:11434", 2.0),
        quiz_model=QUIZ_MODEL,
        tutor_model=TUTOR_MODEL,
        enabled=True,
        quiz_idle_seconds=90.0,
    )
    monkeypatch.setattr(factory, "get_model_residency", lambda: manager)

    response = client.post(RELEASE_URL, headers=teacher_headers)

    assert response.status_code == 200
    by_kind = {item["kind"]: item for item in response.json()["actions"]}
    assert (by_kind["quiz_model"]["target"], by_kind["quiz_model"]["action"]) == (
        QUIZ_MODEL,
        "failed",
    )
    assert (by_kind["tutor_model"]["target"], by_kind["tutor_model"]["action"]) == (
        TUTOR_MODEL,
        "failed",
    )
    assert "unreachable" in by_kind["quiz_model"]["detail"]
    assert ("POST", "/api/generate") in [
        (method, path) for method, path, _ in ollama.requests
    ]
    assert "backend_heap" in {item["kind"] for item in response.json()["actions"]}
