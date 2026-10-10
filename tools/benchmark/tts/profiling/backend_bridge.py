"""The only benchmark module that reaches into the backend core packages."""

from __future__ import annotations

import importlib
import sys
from typing import Any

from tools.benchmark.tts.shared import paths

# The backend packages (core.*) are imported lazily below and live in backend/src,
# so that directory has to be on sys.path before any of them is requested.
if str(paths.BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(paths.BACKEND_SRC))

QWEN_ENGINE_NAMES: tuple[str, ...] = ("qwen3-tts", "qwen")
ONNX_PROVIDER_ENGINE_NAMES: tuple[str, ...] = ("kokoro", "sherpa")
DEFAULT_EXECUTION_PROVIDER: str = "cpu"


def get_tts_router() -> Any:
    """Lazily loads and returns the active backend TTSRouter singleton."""
    router_module = importlib.import_module("core.tts.router")
    return router_module.get_tts_router()


def detect_engine_provider(engine: str) -> str:
    """Returns the resolved execution provider ('cpu' or 'cuda') for an engine."""
    if engine in QWEN_ENGINE_NAMES:
        return _detect_qwen_provider()
    if engine in ONNX_PROVIDER_ENGINE_NAMES:
        return _resolve_configured_provider(engine)
    return DEFAULT_EXECUTION_PROVIDER


def _detect_qwen_provider() -> str:
    """Asks the Qwen model loader which execution provider it resolves to."""
    try:
        qwen_models = importlib.import_module("core.tts.engines.qwen.models")
        return qwen_models.detect_qwen_provider()
    except Exception:  # noqa: BLE001
        # A missing binary or model only means the engine runs on the CPU.
        return DEFAULT_EXECUTION_PROVIDER


def _resolve_configured_provider(engine: str) -> str:
    """Resolves the provider configured for the kokoro or sherpa engine."""
    try:
        config_module = importlib.import_module("core.config")
        provider_module = importlib.import_module("core.tts.engines.provider")
        tts_settings = config_module.get_settings().tts
        configured_provider = (
            tts_settings.kokoro_provider
            if engine == "kokoro"
            else tts_settings.sherpa_provider
        )
        return provider_module.resolve_execution_provider(configured_provider)
    except Exception:  # noqa: BLE001
        # A missing setting or provider module only means the engine runs on the CPU.
        return DEFAULT_EXECUTION_PROVIDER
