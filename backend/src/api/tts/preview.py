"""API router for TTS voice preview synthesis."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.tts.schemas import TTSPreviewRequest
from core.security import AuthContext, require_roles
from core.tts.exceptions import TTSError, TTSUnavailableError
from core.tts.router import get_tts_router

logger = logging.getLogger(__name__)
router = APIRouter()

__all__ = ["router"]

PREVIEW_SAMPLE_TEXT: dict[str, str] = {
    "es": "Hola, esta es la voz de TutorBox para tu clase.",
    "quc": "TutorBox.",
}


@router.post(
    "/preview",
    response_class=Response,
    responses={200: {"content": {"audio/wav": {}}, "description": "WAV audio sample"}},
)
def preview_tts_voice(
    payload: TTSPreviewRequest,
    _ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
) -> Response:
    """Synthesizes a short sample so staff can hear a voice before loading it.

    Loads the target engine on demand and unloads it afterwards when it was
    not already resident, so previews never leave weights in RAM without
    a point. An already-loaded engine is left untouched.
    """
    tts_router = get_tts_router()
    try:
        resolved = tts_router.status(engine=payload.engine, lang=payload.lang)
    except TTSUnavailableError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        ) from err
    was_loaded = bool(resolved["loaded"])
    engine_name: str = resolved["engine"]

    text = (payload.text or "").strip() or PREVIEW_SAMPLE_TEXT[payload.lang]
    try:
        audio = tts_router.synthesize(
            text,
            lang=payload.lang,
            voice=payload.voice,
            backend=payload.engine,
            bypass_cache=True,
        )
    except TTSUnavailableError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err)
        ) from err
    except TTSError as err:
        logger.error("TTS preview synthesis failed: %s", err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err)
        ) from err
    finally:
        if not was_loaded:
            tts_router.unload(engine=engine_name)

    return Response(
        content=audio,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store"},
    )
