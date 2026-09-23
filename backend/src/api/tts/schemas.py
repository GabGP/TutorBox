"""Pydantic schemas for classroom TTS lifecycle endpoints."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "TTSLoadRequest",
    "TTSLoadResponse",
    "TTSPreviewRequest",
    "TTSStatusResponse",
    "TTSUnloadRequest",
    "TTSUnloadResponse",
    "TTSVoiceItem",
]


class TTSLoadRequest(BaseModel):
    """Payload to trigger proactive speech engine model preloading."""

    model_config = ConfigDict(extra="forbid")

    engine: str | None = Field(
        default=None, description="Target engine (piper, espeak, etc.)"
    )
    lang: Literal["es", "quc"] = Field(default="es", description="Language code")
    voice: str | None = Field(default=None, description="Specific voice identifier")


class TTSLoadResponse(BaseModel):
    """Result of engine preloading."""

    engine: str
    loaded: bool
    model_id: str
    load_ms: float


class TTSUnloadRequest(BaseModel):
    """Payload to request unloading model weights from RAM."""

    model_config = ConfigDict(extra="forbid")

    engine: str | None = Field(
        default=None, description="Engine to unload (None for all)"
    )


class TTSUnloadResponse(BaseModel):
    """Result of engine unloading."""

    engine: str
    loaded: bool = False


class TTSPreviewRequest(BaseModel):
    """Payload to synthesize a short voice sample for A/B listening."""

    model_config = ConfigDict(extra="forbid")

    engine: str | None = Field(
        default=None, description="Target engine (piper, espeak, etc.)"
    )
    lang: Literal["es", "quc"] = Field(default="es", description="Language code")
    voice: str | None = Field(default=None, description="Specific voice identifier")
    text: str | None = Field(
        default=None,
        max_length=200,
        description="Custom sample text (defaults per language)",
    )


class TTSStatusResponse(BaseModel):
    """Current memory residency and active model status."""

    engine: str
    loaded: bool
    model_id: str


class TTSVoiceItem(BaseModel):
    """Voice metadata descriptor."""

    id: str
    lang: str
    engine: str
