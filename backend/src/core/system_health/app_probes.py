"""What the application itself holds in memory: the Ollama models and the voice engines."""

import logging
from typing import Protocol

from core.config import Settings, get_settings
from core.llm.residency.models import ResidencyError
from core.llm.residency.ollama_client import OllamaResidencyClient, ollama_server_root
from core.system_health.models import ModelReading
from core.tts.router import get_tts_router

__all__ = [
    "ENGINES_WITHOUT_WEIGHTS",
    "list_resident_models",
    "loaded_voice_engines",
    "models_in_memory_from_settings",
    "residency_client_from_settings",
    "resident_model_names_from_settings",
]

logger = logging.getLogger(__name__)


class ModelQueries(Protocol):
    """The two questions the panel asks Ollama (OllamaResidencyClient, or a fake in tests)."""

    def resident_models(self) -> set[str]: ...

    def gpu_percent(self, model_name: str) -> int | None: ...


# eSpeak NG runs a small process per sentence and keeps nothing in memory, but its router entry
# reports "loaded" whenever it is installed: it is neither a loaded voice nor something to free.
ENGINES_WITHOUT_WEIGHTS = frozenset({"espeak"})

# A health panel must not wait out the generation timeout (60 s) while Ollama hangs.
HEALTH_PROBE_TIMEOUT_SECONDS = 2.0


def residency_client_from_settings(settings: Settings) -> OllamaResidencyClient | None:
    """A client for Ollama's model API, or None when SLM_MANAGE_RESIDENCY is off (Ollama is not asked)."""
    if not settings.llm.manage_residency:
        return None
    return OllamaResidencyClient(
        ollama_server_root(settings.llm.base_url), HEALTH_PROBE_TIMEOUT_SECONDS
    )


def models_in_memory_from_settings() -> list[ModelReading]:
    """The models Ollama holds now; empty when residency is off or Ollama does not answer."""
    client = residency_client_from_settings(get_settings())
    return [] if client is None else list_resident_models(client)


def resident_model_names_from_settings() -> set[str] | None:
    """Names Ollama holds now, or None when that is unknown (residency off, Ollama down)."""
    client = residency_client_from_settings(get_settings())
    if client is None:
        return None
    try:
        return client.resident_models()
    except ResidencyError as error:
        logger.info("Memory release: Ollama models unknown: %s", error)
        return None


def list_resident_models(client: ModelQueries) -> list[ModelReading]:
    """Each resident model by name, with its GPU share; a model whose share fails shows None."""
    try:
        names = sorted(client.resident_models())
    except ResidencyError as error:
        logger.info("Health panel: Ollama models unavailable: %s", error)
        return []
    return [
        ModelReading(name=name, gpu_percent=_gpu_percent_or_none(client, name))
        for name in names
    ]


def loaded_voice_engines() -> list[str]:
    """Canonical names of the voice engines with weights in memory; empty when the router fails."""
    try:
        engines = get_tts_router().loaded_engines()
    except Exception:
        logger.warning("Health panel: voice engines unavailable", exc_info=True)
        return []
    return [engine for engine in engines if engine not in ENGINES_WITHOUT_WEIGHTS]


def _gpu_percent_or_none(client: ModelQueries, name: str) -> int | None:
    try:
        return client.gpu_percent(name)
    except ResidencyError:
        return None
