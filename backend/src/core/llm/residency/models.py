"""What a model residency request reports, and the errors that can stop one."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

__all__ = [
    "ModelResidencyResult",
    "ResidencyAction",
    "ResidencyError",
    "ResidencyUnsupported",
]

# loaded / unloaded: the request worked. failed: the server could not do it.
# unsupported: the server is not Ollama. kept: another part of the app still needs the model.
# disabled: SLM_MANAGE_RESIDENCY is off, so nothing was asked of the server.
ResidencyAction = Literal[
    "loaded", "unloaded", "kept", "unsupported", "failed", "disabled"
]


class ModelResidencyResult(BaseModel):
    """One model's outcome. `detail` is for logs and tests, never shown to students."""

    model_config = ConfigDict(frozen=True)

    model: str
    action: ResidencyAction
    duration_ms: float | None = None
    detail: str | None = None
    # After a load: the share of the model Ollama placed on the GPU. Below 100 the rest
    # runs on the CPU, several times slower (the Jetson had too little free memory).
    gpu_percent: int | None = None


class ResidencyError(Exception):
    """The Ollama server could not answer a residency request (down, slow or refusing)."""


class ResidencyUnsupported(ResidencyError):
    """The server at SLM_BASE_URL has no Ollama model API (llama.cpp, LM Studio, ...)."""
