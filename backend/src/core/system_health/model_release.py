"""Frees the quiz model unless a question is being generated, then applies the saved mode to the tutor model."""

import logging
from collections.abc import Callable

from core.db.mode_repository import ApplianceMode
from core.llm.residency.manager import ModelResidencyManager
from core.llm.residency.models import ModelResidencyResult
from core.system_health.release_report import ReleaseAction, ReleaseKind

__all__ = ["release_models"]

logger = logging.getLogger(__name__)


def release_models(
    residency: ModelResidencyManager,
    *,
    quiz_model_name: str,
    read_saved_mode: Callable[[], ApplianceMode],
    tutor_model_name: str | None = None,
    read_resident: Callable[[], set[str] | None] = lambda: None,
) -> list[ReleaseAction]:
    """Quiz model first, then the tutor model: unloaded outside tutor mode, loaded back inside it.

    With `read_resident` (Ollama's /api/ps), a model that is not in memory is left out of the
    report, so the teacher is not told that something was unloaded when nothing was. None (the
    list is unknown) reports every step, as unloading a model that is not loaded is harmless.
    """
    resident = read_resident()
    actions: list[ReleaseAction] = []
    if resident is None or quiz_model_name in resident:
        actions.append(_release_quiz(residency, quiz_model_name))
    tutor_step = _apply_saved_mode(residency, read_saved_mode)
    tutor_was_absent = resident is not None and tutor_model_name not in resident
    if not (tutor_was_absent and tutor_step.action == "unloaded"):
        actions.append(tutor_step)
    return actions


def _release_quiz(
    residency: ModelResidencyManager, quiz_model_name: str
) -> ReleaseAction:
    if residency.quiz_generation_in_flight():
        return ReleaseAction(
            target=quiz_model_name,
            kind="quiz_model",
            action="kept",
            detail="a question generation is running",
        )
    return _from_residency("quiz_model", residency.release_quiz())


def _apply_saved_mode(
    residency: ModelResidencyManager, read_saved_mode: Callable[[], ApplianceMode]
) -> ReleaseAction:
    try:
        saved_mode = read_saved_mode()
    except Exception as error:
        logger.warning("Memory release: saved mode unknown: %s", error, exc_info=True)
        return ReleaseAction(
            target="modelo del tutor",
            kind="tutor_model",
            action="failed",
            detail=f"the saved mode could not be read: {error}",
        )
    return _from_residency("tutor_model", residency.apply_mode(saved_mode))


def _from_residency(kind: ReleaseKind, result: ModelResidencyResult) -> ReleaseAction:
    return ReleaseAction(
        target=result.model,
        kind=kind,
        action=result.action,
        detail=result.detail,
    )
