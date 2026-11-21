"""Runs the memory release phases in order, waits for the RAM to settle and reports what came back."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from core.system_health.release_report import (
    MemoryReleaseReport,
    ReleaseAction,
    ReleaseKind,
)

__all__ = ["MemoryReleaser", "ReleasePhase"]

logger = logging.getLogger(__name__)

# Ollama and the voices give memory back a moment after they are told to; this is that moment.
RELEASE_SETTLE_SECONDS = 1.0


@dataclass(frozen=True)
class ReleasePhase:
    """One step of a release. A step that raises is reported as failed, never re-raised."""

    target: str
    kind: ReleaseKind
    run: Callable[[], list[ReleaseAction]]


class MemoryReleaser:
    """Reads the available RAM, runs every phase, waits, reads it again and drops the stale snapshot."""

    def __init__(
        self,
        *,
        phases: list[ReleasePhase],
        read_available_mb: Callable[[], float | None],
        invalidate_snapshot: Callable[[], None],
        settle_seconds: float = RELEASE_SETTLE_SECONDS,
    ) -> None:
        self._phases = phases
        self._read_available_mb = read_available_mb
        self._invalidate_snapshot = invalidate_snapshot
        self._settle_seconds = settle_seconds

    def release(self) -> MemoryReleaseReport:
        """Never raises: a failing phase becomes a `failed` action and the others still run."""
        available_before_mb = self._read_available_mb()
        actions = [
            action for phase in self._phases for action in self._run_phase(phase)
        ]
        time.sleep(self._settle_seconds)
        available_after_mb = self._read_available_mb()
        self._invalidate_snapshot()
        freed_mb = (
            None
            if available_before_mb is None or available_after_mb is None
            else round(available_after_mb - available_before_mb, 1)
        )
        return MemoryReleaseReport(
            available_before_mb=available_before_mb,
            available_after_mb=available_after_mb,
            freed_mb=freed_mb,
            actions=actions,
        )

    def _run_phase(self, phase: ReleasePhase) -> list[ReleaseAction]:
        try:
            return phase.run()
        except Exception as error:
            logger.warning(
                "Memory release step %s failed: %s", phase.target, error, exc_info=True
            )
            return [
                ReleaseAction(
                    target=phase.target,
                    kind=phase.kind,
                    action="failed",
                    detail=str(error),
                )
            ]
