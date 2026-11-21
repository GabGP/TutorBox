"""get_model_residency and build_model_residency (core/llm/residency/factory.py)."""

import pytest

from core.llm.residency import factory
from core.llm.residency.manager import ModelResidencyManager
from core.llm.residency.ollama_client import OllamaResidencyClient


@pytest.fixture(autouse=True)
def fresh_singleton(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(factory, "_manager", None)
    monkeypatch.delenv("SLM_MANAGE_RESIDENCY", raising=False)
    monkeypatch.delenv("SLM_QUIZ_IDLE_UNLOAD_SECONDS", raising=False)
    yield
    monkeypatch.setattr(factory, "_manager", None)


def test_the_manager_is_built_once_from_the_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SLM_BASE_URL", "http://10.0.0.5:11434/v1")
    monkeypatch.setenv("SLM_MODEL_NAME", "qwen2.5:3b")
    monkeypatch.setenv("TUTOR_MODEL_NAME", "tutor:latest")
    monkeypatch.setenv("SLM_MANAGE_RESIDENCY", "true")
    monkeypatch.setenv("SLM_QUIZ_IDLE_UNLOAD_SECONDS", "45")

    first = factory.get_model_residency()
    second = factory.get_model_residency()

    assert first is second
    assert isinstance(first, ModelResidencyManager)
    assert first.enabled is True
    assert first._quiz_model == "qwen2.5:3b"
    assert first._tutor_model == "tutor:latest"
    assert first._quiz_hold._idle_seconds == 45.0
    assert isinstance(first._client, OllamaResidencyClient)
    assert first._client._root == "http://10.0.0.5:11434"


def test_switch_off_builds_a_disabled_manager(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SLM_MANAGE_RESIDENCY", "false")

    assert factory.get_model_residency().enabled is False


def test_the_tutor_model_defaults_to_the_deepseek_distill(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("TUTOR_MODEL_NAME", "")

    manager = factory.build_model_residency()

    assert manager._tutor_model.startswith(
        "hf.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF"
    )
