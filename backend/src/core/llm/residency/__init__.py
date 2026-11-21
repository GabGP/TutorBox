"""Model residency: keeps the Ollama models in memory only while the classroom needs them."""

from core.llm.residency.factory import get_model_residency
from core.llm.residency.manager import ModelResidencyManager
from core.llm.residency.models import (
    ModelResidencyResult,
    ResidencyAction,
    ResidencyError,
    ResidencyUnsupported,
)
from core.llm.residency.ollama_client import OllamaResidencyClient, ollama_server_root
from core.llm.residency.startup import start_residency_reconcile

__all__ = [
    "ModelResidencyManager",
    "ModelResidencyResult",
    "OllamaResidencyClient",
    "ResidencyAction",
    "ResidencyError",
    "ResidencyUnsupported",
    "get_model_residency",
    "ollama_server_root",
    "start_residency_reconcile",
]
