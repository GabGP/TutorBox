"""What a memory release did: what was unloaded, what was loaded back, and how much RAM came back."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from core.llm.residency.models import ResidencyAction

__all__ = ["MemoryReleaseReport", "ReleaseAction", "ReleaseKind"]

ReleaseKind = Literal["quiz_model", "tutor_model", "voice", "backend_heap"]


class ReleaseAction(BaseModel):
    """One thing the release did, or chose not to do, to a model, a voice or the backend heap."""

    model_config = ConfigDict(frozen=True)

    target: str = Field(
        description="The model name, 'voz <engine>' or 'heap del proceso'."
    )
    kind: ReleaseKind
    action: ResidencyAction
    detail: str | None = Field(
        default=None, description="For logs; the panel shows the rest."
    )


class MemoryReleaseReport(BaseModel):
    """RAM available before and after the release (MB, None when unreadable) and the actions taken."""

    model_config = ConfigDict(frozen=True)

    available_before_mb: float | None
    available_after_mb: float | None
    freed_mb: float | None = Field(
        description="After minus before; can be negative if others used RAM meanwhile."
    )
    actions: list[ReleaseAction]
