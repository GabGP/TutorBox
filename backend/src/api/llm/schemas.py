"""Pydantic schemas for local LLM lifecycle endpoints."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "LLMActionResponse",
    "LLMLoadRequest",
    "LLMStatusResponse",
]


class LLMLoadRequest(BaseModel):
    """Payload to trigger LLM model loading into GPU/RAM."""

    model_config = ConfigDict(extra="forbid")

    model: str | None = Field(
        default=None, description="Optional model identifier or path"
    )


class LLMActionResponse(BaseModel):
    """Result of LLM lifecycle action (load/unload)."""

    status: str
    detail: str | None = None


class LLMStatusResponse(BaseModel):
    """Current model residency status from local llama-server."""

    status: str
    models: list[dict[str, Any]] = Field(default_factory=list)
