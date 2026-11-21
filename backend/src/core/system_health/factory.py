"""The one Jetson health service of this process, built from the appliance settings."""

import threading
from pathlib import Path

from core.config import get_settings
from core.config.tutor_settings import load_tutor_config
from core.db.database import get_db_path
from core.llm.residency.factory import get_model_residency
from core.system_health.app_probes import (
    loaded_voice_engines,
    models_in_memory_from_settings,
    resident_model_names_from_settings,
)
from core.system_health.appliance_state import quiz_game_running, read_saved_mode
from core.system_health.files import HOST_ROOT
from core.system_health.heap import trim_backend_heap
from core.system_health.memory import read_memory
from core.system_health.memory_release import MemoryReleaser, ReleasePhase
from core.system_health.model_release import release_models
from core.system_health.service import SystemHealthService
from core.system_health.voice_release import release_voices
from core.tts.router.router import get_tts_router

__all__ = [
    "build_memory_releaser",
    "build_system_health_service",
    "get_memory_releaser",
    "get_system_health_service",
]

_service_lock = threading.Lock()
_service: SystemHealthService | None = None


def get_system_health_service() -> SystemHealthService:
    """Returns the process-wide service, built on first use (thread-safe)."""
    global _service
    with _service_lock:
        if _service is None:
            _service = build_system_health_service()
        return _service


def build_system_health_service() -> SystemHealthService:
    """The service for this appliance: the host's files and the folder of the database."""
    return SystemHealthService(
        root=HOST_ROOT,
        data_directory=Path(get_db_path()).parent,
        models_in_memory=models_in_memory_from_settings,
        voices_loaded=loaded_voice_engines,
    )


def get_memory_releaser() -> MemoryReleaser:
    """The release for this request; it holds no state of its own, so it is built per call."""
    return build_memory_releaser(get_system_health_service())


def build_memory_releaser(service: SystemHealthService) -> MemoryReleaser:
    """Quiz and tutor models, then voices, then the backend heap; the snapshot is dropped at the end."""
    return MemoryReleaser(
        phases=[
            ReleasePhase(
                target="modelos",
                kind="quiz_model",
                run=lambda: release_models(
                    get_model_residency(),
                    quiz_model_name=get_settings().llm.model_name,
                    read_saved_mode=read_saved_mode,
                    tutor_model_name=load_tutor_config().model_name,
                    read_resident=resident_model_names_from_settings,
                ),
            ),
            ReleasePhase(
                target="voces",
                kind="voice",
                run=lambda: release_voices(get_tts_router(), quiz_game_running),
            ),
            ReleasePhase(
                target="heap del proceso",
                kind="backend_heap",
                run=lambda: [trim_backend_heap()],
            ),
        ],
        read_available_mb=_available_mb,
        invalidate_snapshot=service.invalidate,
    )


def _available_mb() -> float | None:
    reading = read_memory(HOST_ROOT)
    return None if reading is None else reading.available_mb
