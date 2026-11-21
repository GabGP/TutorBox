"""Unloads the loaded voices, unless a live quiz game needs them; the speech endpoint loads them again."""

import logging
from collections.abc import Callable
from typing import Protocol

from core.llm.residency.models import ResidencyAction
from core.system_health.app_probes import ENGINES_WITHOUT_WEIGHTS
from core.system_health.release_report import ReleaseAction

__all__ = ["release_voices"]

logger = logging.getLogger(__name__)

UNKNOWN_VOICES_TARGET = "voces"


class VoiceRouter(Protocol):
    """The two calls the release makes on the TTS router (TTSRouter, or a fake in tests)."""

    def loaded_engines(self) -> list[str]: ...

    def unload(self, engine: str | None = None) -> str: ...


def release_voices(
    router: VoiceRouter, game_running: Callable[[], bool]
) -> list[ReleaseAction]:
    """One action per loaded voice engine. A game in progress keeps its voices (`kept`)."""
    try:
        engines = [
            engine
            for engine in router.loaded_engines()
            if engine not in ENGINES_WITHOUT_WEIGHTS
        ]
    except Exception as error:
        logger.warning("Health panel: loaded voices unknown: %s", error, exc_info=True)
        return [
            _voice_action(
                UNKNOWN_VOICES_TARGET, "failed", f"loaded voices unknown: {error}"
            )
        ]
    if not engines:
        return []
    try:
        running = game_running()
        reason = "a quiz game is running" if running else None
    except Exception as error:
        logger.warning("Health panel: game state unknown: %s", error, exc_info=True)
        running, reason = True, f"game state unknown, voices kept: {error}"
    if running:
        return [_voice_action(f"voz {engine}", "kept", reason) for engine in engines]
    return [_unload(router, engine) for engine in engines]


def _unload(router: VoiceRouter, engine: str) -> ReleaseAction:
    target = f"voz {engine}"
    try:
        router.unload(engine=engine)
    except Exception as error:
        logger.warning(
            "Health panel: %s not unloaded: %s", target, error, exc_info=True
        )
        return _voice_action(target, "failed", str(error))
    return _voice_action(target, "unloaded", None)


def _voice_action(
    target: str, action: ResidencyAction, detail: str | None
) -> ReleaseAction:
    return ReleaseAction(target=target, kind="voice", action=action, detail=detail)
