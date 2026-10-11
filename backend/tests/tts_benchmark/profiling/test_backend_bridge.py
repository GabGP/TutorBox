"""Verifies the backend bridge puts core.* on sys.path and resolves engine providers safely."""

import importlib
import sys
import types

import pytest

from tools.benchmark.tts.profiling import backend_bridge
from tools.benchmark.tts.shared import paths

BACKEND_SOURCE_TEXT = str(paths.BACKEND_SRC)


def _always_raise(*_arguments, **_keyword_arguments):
    """Stands in for a backend call that fails, such as a missing binary."""
    raise RuntimeError("backend unavailable")


def _install_stub_module(monkeypatch, module_name: str, **attributes) -> None:
    """Registers a stub under module_name so importlib returns it without touching backend/src."""
    monkeypatch.setitem(sys.modules, module_name, types.SimpleNamespace(**attributes))


def _install_provider_stubs(
    monkeypatch, kokoro_provider: str, sherpa_provider: str
) -> list[str]:
    """Stubs core.config and the provider resolver, returning the list the resolver records into."""
    requested_providers: list[str] = []

    def resolve_execution_provider(requested: str) -> str:
        requested_providers.append(requested)
        return f"resolved-{requested}"

    settings = types.SimpleNamespace(
        tts=types.SimpleNamespace(
            kokoro_provider=kokoro_provider, sherpa_provider=sherpa_provider
        )
    )
    _install_stub_module(monkeypatch, "core.config", get_settings=lambda: settings)
    _install_stub_module(
        monkeypatch,
        "core.tts.engines.provider",
        resolve_execution_provider=resolve_execution_provider,
    )
    return requested_providers


def test_backend_source_directory_is_on_sys_path_after_import():
    """Verifies importing the bridge leaves backend/src on sys.path."""
    assert BACKEND_SOURCE_TEXT in sys.path


def test_reload_puts_backend_source_directory_back_when_missing(monkeypatch):
    """Verifies reloading the bridge inserts backend/src at the front of a sys.path that lacks it."""
    monkeypatch.setattr(sys, "path", ["unrelated-entry"])
    importlib.reload(backend_bridge)
    assert sys.path == [BACKEND_SOURCE_TEXT, "unrelated-entry"]


def test_reload_keeps_a_single_backend_source_entry_when_present(monkeypatch):
    """Verifies reloading the bridge does not add a second copy of backend/src."""
    monkeypatch.setattr(sys, "path", [BACKEND_SOURCE_TEXT, "unrelated-entry"])
    importlib.reload(backend_bridge)
    assert sys.path == [BACKEND_SOURCE_TEXT, "unrelated-entry"]


def test_get_tts_router_returns_the_router_from_core_tts_router(monkeypatch):
    """Verifies get_tts_router returns whatever core.tts.router hands back."""
    router_sentinel = object()
    _install_stub_module(
        monkeypatch, "core.tts.router", get_tts_router=lambda: router_sentinel
    )
    assert backend_bridge.get_tts_router() is router_sentinel


@pytest.mark.parametrize("engine_name", ["qwen3-tts", "qwen"])
def test_qwen_engines_report_the_detected_qwen_provider(monkeypatch, engine_name):
    """Verifies both Qwen engine names report the provider the Qwen loader detects."""
    _install_stub_module(
        monkeypatch,
        "core.tts.engines.qwen.models",
        detect_qwen_provider=lambda: "cuda",
    )
    assert backend_bridge.detect_engine_provider(engine_name) == "cuda"


def test_failing_qwen_detection_falls_back_to_cpu(monkeypatch):
    """Verifies a raising Qwen provider lookup reports the CPU provider."""
    _install_stub_module(
        monkeypatch,
        "core.tts.engines.qwen.models",
        detect_qwen_provider=_always_raise,
    )
    assert backend_bridge.detect_engine_provider("qwen3-tts") == "cpu"


def test_missing_qwen_module_falls_back_to_cpu(monkeypatch):
    """Verifies a Qwen module that cannot be imported reports the CPU provider."""
    monkeypatch.setitem(sys.modules, "core.tts.engines.qwen.models", None)
    assert backend_bridge.detect_engine_provider("qwen") == "cpu"


def test_kokoro_resolves_the_kokoro_provider_setting(monkeypatch):
    """Verifies kokoro passes kokoro_provider to the resolver and returns its answer."""
    requested_providers = _install_provider_stubs(
        monkeypatch, kokoro_provider="cuda", sherpa_provider="cpu"
    )
    assert backend_bridge.detect_engine_provider("kokoro") == "resolved-cuda"
    assert requested_providers == ["cuda"]


def test_sherpa_resolves_the_sherpa_provider_setting(monkeypatch):
    """Verifies sherpa passes sherpa_provider to the resolver and returns its answer."""
    requested_providers = _install_provider_stubs(
        monkeypatch, kokoro_provider="cuda", sherpa_provider="cpu"
    )
    assert backend_bridge.detect_engine_provider("sherpa") == "resolved-cpu"
    assert requested_providers == ["cpu"]


def test_failing_provider_resolution_falls_back_to_cpu(monkeypatch):
    """Verifies a raising provider resolver reports the CPU provider."""
    _install_stub_module(
        monkeypatch,
        "core.config",
        get_settings=lambda: types.SimpleNamespace(
            tts=types.SimpleNamespace(kokoro_provider="cuda", sherpa_provider="cuda")
        ),
    )
    _install_stub_module(
        monkeypatch,
        "core.tts.engines.provider",
        resolve_execution_provider=_always_raise,
    )
    assert backend_bridge.detect_engine_provider("sherpa") == "cpu"


def test_unreadable_settings_fall_back_to_cpu_without_resolving(monkeypatch):
    """Verifies a raising get_settings reports the CPU provider and skips the resolver."""
    requested_providers = _install_provider_stubs(
        monkeypatch, kokoro_provider="cuda", sherpa_provider="cuda"
    )
    _install_stub_module(monkeypatch, "core.config", get_settings=_always_raise)
    assert backend_bridge.detect_engine_provider("kokoro") == "cpu"
    assert requested_providers == []


@pytest.mark.parametrize("engine_name", ["piper", "espeak", "melo"])
def test_engines_without_a_provider_setting_report_cpu_without_backend_imports(
    monkeypatch, engine_name
):
    """Verifies engines outside the Qwen, kokoro and sherpa families never consult core.*."""
    _install_stub_module(
        monkeypatch, "core.tts.engines.qwen.models", detect_qwen_provider=_always_raise
    )
    _install_stub_module(monkeypatch, "core.config", get_settings=_always_raise)
    _install_stub_module(
        monkeypatch,
        "core.tts.engines.provider",
        resolve_execution_provider=_always_raise,
    )
    assert backend_bridge.detect_engine_provider(engine_name) == "cpu"
