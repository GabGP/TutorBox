"""API router exposing explicit quiz-agnostic TTS lifecycle operations."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.tts.schemas import (
    TTSLoadRequest,
    TTSLoadResponse,
    TTSStatusResponse,
    TTSUnloadRequest,
    TTSUnloadResponse,
    TTSVoiceItem,
)
from core.config import get_settings
from core.security import AuthContext, require_roles
from core.tts.exceptions import TTSUnavailableError
from core.tts.router import get_tts_router

logger = logging.getLogger(__name__)
router = APIRouter()

__all__ = ["router"]


@router.post(
    "/load",
    response_model=TTSLoadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def load_tts_engine(
    payload: TTSLoadRequest,
    _ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
) -> TTSLoadResponse:
    """Proactively preloads TTS voice weights to prepare for classroom speech."""
    tts_router = get_tts_router()
    try:
        engine, load_ms = tts_router.preload(
            engine=payload.engine, lang=payload.lang, voice=payload.voice
        )
        current_status = tts_router.status(engine=engine, lang=payload.lang)
    except TTSUnavailableError as err:
        logger.warning("TTS load failed for %s: %s", payload.engine, err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err)
        ) from err

    return TTSLoadResponse(
        engine=engine,
        loaded=current_status["loaded"],
        model_id=current_status["model_id"],
        load_ms=round(load_ms, 2),
    )


@router.post(
    "/unload",
    response_model=TTSUnloadResponse,
    status_code=status.HTTP_200_OK,
)
def unload_tts_engine(
    _ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    payload: TTSUnloadRequest | None = None,
) -> TTSUnloadResponse:
    """Reclaims RAM by unloading TTS model weights from memory."""
    target_engine = payload.engine if payload else None
    tts_router = get_tts_router()
    unloaded = tts_router.unload(engine=target_engine)
    return TTSUnloadResponse(engine=unloaded, loaded=False)


@router.get(
    "/status",
    response_model=TTSStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_tts_status(
    _ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    engine: str | None = None,
    lang: str = "es",
) -> TTSStatusResponse:
    """Returns memory residency and active model status for speech synthesis."""
    tts_router = get_tts_router()
    try:
        current_status = tts_router.status(engine=engine, lang=lang)
    except TTSUnavailableError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        ) from err
    return TTSStatusResponse(
        engine=current_status["engine"],
        loaded=current_status["loaded"],
        model_id=current_status["model_id"],
    )


@router.get(
    "/voices",
    response_model=list[TTSVoiceItem],
    status_code=status.HTTP_200_OK,
)
def list_tts_voices(
    _ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    lang: str = "es",
    engine: str | None = None,
) -> list[TTSVoiceItem]:
    """Lists available voice identifiers for comparative A/B and pedagogical selection."""
    tts = get_settings().tts
    voices: list[TTSVoiceItem] = []
    if lang == "es":
        voices.append(TTSVoiceItem(id=tts.piper_model_es, lang="es", engine="piper"))
        voices.append(TTSVoiceItem(id=tts.voice, lang="es", engine="espeak"))
        if tts.sherpa_model_es:
            voices.append(
                TTSVoiceItem(id=tts.sherpa_model_es, lang="es", engine="sherpa")
            )
        if tts.kokoro_voice:
            voices.append(TTSVoiceItem(id=tts.kokoro_voice, lang="es", engine="kokoro"))
    elif lang == "quc":
        voices.append(TTSVoiceItem(id=tts.piper_model_quc, lang="quc", engine="piper"))
        if tts.voice_quc:
            voices.append(TTSVoiceItem(id=tts.voice_quc, lang="quc", engine="espeak"))

    if engine:
        voices = [v for v in voices if v.engine.lower() == engine.lower()]
    return voices
