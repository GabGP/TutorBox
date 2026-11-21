"""SLM_MANAGE_RESIDENCY and SLM_QUIZ_IDLE_UNLOAD_SECONDS (core/config/settings.py)."""

import pytest

from core.config import (
    DEFAULT_SLM_MANAGE_RESIDENCY,
    DEFAULT_SLM_QUIZ_IDLE_UNLOAD_SECONDS,
    get_settings,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("SLM_MANAGE_RESIDENCY", raising=False)
    monkeypatch.delenv("SLM_QUIZ_IDLE_UNLOAD_SECONDS", raising=False)


def test_residency_defaults_to_managed_with_a_ninety_second_idle_unload():
    llm = get_settings(reload=True).llm

    assert llm.manage_residency is DEFAULT_SLM_MANAGE_RESIDENCY is True
    assert llm.quiz_idle_unload_seconds == DEFAULT_SLM_QUIZ_IDLE_UNLOAD_SECONDS == 90.0


def test_residency_can_be_switched_off_and_the_idle_time_changed(monkeypatch):
    monkeypatch.setenv("SLM_MANAGE_RESIDENCY", "no")
    monkeypatch.setenv("SLM_QUIZ_IDLE_UNLOAD_SECONDS", "30")

    llm = get_settings(reload=True).llm

    assert llm.manage_residency is False
    assert llm.quiz_idle_unload_seconds == 30.0


@pytest.mark.parametrize("raw_idle", ["0.5", "soon", ""])
def test_invalid_idle_time_falls_back_to_the_default(monkeypatch, raw_idle):
    monkeypatch.setenv("SLM_QUIZ_IDLE_UNLOAD_SECONDS", raw_idle)

    assert get_settings(reload=True).llm.quiz_idle_unload_seconds == 90.0


def test_unrecognised_switch_value_keeps_the_default(monkeypatch):
    monkeypatch.setenv("SLM_MANAGE_RESIDENCY", "maybe")

    assert get_settings(reload=True).llm.manage_residency is True
