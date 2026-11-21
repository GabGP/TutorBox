"""The one residency manager of this process, configured from SLM_* and TUTOR_* settings."""

import threading

from core.config import get_settings
from core.config.tutor_settings import load_tutor_config
from core.llm.residency.manager import ModelResidencyManager
from core.llm.residency.ollama_client import OllamaResidencyClient, ollama_server_root

__all__ = ["build_model_residency", "get_model_residency"]

_manager_lock = threading.Lock()
_manager: ModelResidencyManager | None = None


def get_model_residency() -> ModelResidencyManager:
    """Returns the process-wide manager, built on first use (thread-safe)."""
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = build_model_residency()
        return _manager


def build_model_residency() -> ModelResidencyManager:
    """Builds a manager from the current settings (the quiz model is SLM_MODEL_NAME)."""
    llm_settings = get_settings(reload=True).llm
    client = OllamaResidencyClient(
        ollama_server_root(llm_settings.base_url), llm_settings.timeout_seconds
    )
    return ModelResidencyManager(
        client,
        quiz_model=llm_settings.model_name,
        tutor_model=load_tutor_config().model_name,
        enabled=llm_settings.manage_residency,
        quiz_idle_seconds=llm_settings.quiz_idle_unload_seconds,
    )
