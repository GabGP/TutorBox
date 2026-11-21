"""Turns one request to Ollama into a result: a refused or unreachable server is not an exception."""

import logging
from collections.abc import Callable
from typing import Literal

from core.llm.residency.models import (
    ModelResidencyResult,
    ResidencyAction,
    ResidencyError,
    ResidencyUnsupported,
)

logger = logging.getLogger(__name__)

__all__ = ["attempt_request", "outcome", "with_gpu_share"]


def outcome(
    model_name: str, action: ResidencyAction, detail: str | None = None
) -> ModelResidencyResult:
    """A result that made no request, or whose request did not succeed."""
    return ModelResidencyResult(model=model_name, action=action, detail=detail)


def attempt_request(
    model_name: str,
    success_action: Literal["loaded", "unloaded"],
    request: Callable[[], float | None],
) -> ModelResidencyResult:
    """Runs `request` (it returns the load time in ms, or None) and reports what happened."""
    try:
        duration_ms = request()
    except ResidencyUnsupported as error:
        logger.info("Model %s is not managed: %s", model_name, error)
        return outcome(model_name, "unsupported", str(error))
    except ResidencyError as error:
        logger.warning("Model %s was not %s: %s", model_name, success_action, error)
        return outcome(model_name, "failed", str(error))
    logger.info("Model %s %s.", model_name, success_action)
    return ModelResidencyResult(
        model=model_name, action=success_action, duration_ms=duration_ms
    )


def with_gpu_share(
    result: ModelResidencyResult, read_gpu_percent: Callable[[], int | None]
) -> ModelResidencyResult:
    """Adds how much of a just-loaded model is on the GPU; a model partly on the CPU is slow."""
    if result.action != "loaded":
        return result
    try:
        gpu_percent = read_gpu_percent()
    except ResidencyError as error:
        logger.warning("Could not read where %s was placed: %s", result.model, error)
        return result
    if gpu_percent is not None and gpu_percent < 100:
        logger.warning(
            "Model %s is only %d%% on the GPU; the rest runs on the CPU, slowly.",
            result.model,
            gpu_percent,
        )
    return result.model_copy(update={"gpu_percent": gpu_percent})
