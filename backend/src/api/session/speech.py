"""Spoken >51% intervention audio for the teacher's device.

The teacher's browser cannot be trusted with the pedagogical rule, so this endpoint recomputes
the tally and the decision server-side and only returns audio when a single distractor really
did take more than 51% of the class. Synthesis is delegated to the pluggable offline TTS engine.
"""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.session.dependencies import get_session_and_current_round
from core.db.database import get_db
from core.db.question_repository import get_question_by_id
from core.db.vote_repository import get_votes_for_round
from core.security import AuthContext, require_roles
from core.tts import (
    TTSSynthesisError,
    TTSUnavailableError,
    clear_speech_cache,
    get_tts_router,
    synthesize_speech,
)
from modes.quiz.session.evaluator import evaluate_round_outcome
from modes.quiz.session.models import RoundStatus
from modes.quiz.session.speech import build_intervention_script

logger = logging.getLogger(__name__)
router = APIRouter()

SpeechLanguage = Literal["es", "quc"]

__all__ = ["SpeechLanguage", "clear_speech_cache", "round_speech", "router"]


@router.get(
    "/{session_id}/speech",
    response_class=Response,
    responses={200: {"content": {"audio/wav": {}}, "description": "WAV audio stream"}},
)
def round_speech(
    session_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    lang: SpeechLanguage = "es",
    engine: str | None = None,
    voice: str | None = None,
) -> Response:
    """Synthesizes the misconception explanation for the current revealed round.

    Optional engine/voice select the teacher's saved voice; without them
    the configured default engine speaks.
    """
    with get_db() as conn:
        _, current_round = get_session_and_current_round(conn, session_id)
        if current_round.status not in (
            RoundStatus.CLOSED.value,
            RoundStatus.REVEALED.value,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Round voting has not finished yet.",
            )
        question = (
            get_question_by_id(conn, current_round.question_id)
            if current_round.question_id
            else None
        )
        if question is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question for this round was not found.",
            )
        votes = get_votes_for_round(conn, current_round.id)

    tally, decision = evaluate_round_outcome(
        votes, question.correct_option, question.distractors
    )
    if not decision.should_speak:
        logger.info(
            "Speech skipped for round %s (status=%s, reason=%s)",
            current_round.id,
            current_round.status,
            decision.reason,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The >51% rule did not trigger for this round ({decision.reason}).",
        )

    logger.info(
        "Starting speech synthesis for round %s (dominant=%s, pct=%.1f%%, lang=%s, engine=%s)",
        current_round.id,
        decision.dominant_distractor,
        decision.dominant_percentage,
        lang,
        engine or "default",
    )
    script = build_intervention_script(question.options, tally, decision)
    try:
        if engine or voice:
            audio = get_tts_router().synthesize(
                script, lang=lang, voice=voice, backend=engine
            )
        else:
            audio = synthesize_speech(script, lang=lang)
    except TTSUnavailableError as err:
        logger.warning("Speech unavailable for session %s: %s", session_id, err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err)
        ) from err
    except TTSSynthesisError as err:
        logger.error("Speech synthesis failed for session %s: %s", session_id, err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err)
        ) from err

    logger.info(
        "Synthesized >51%% audio ready for round %s (%d bytes WAV)",
        current_round.id,
        len(audio),
    )
    return Response(
        content=audio,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store"},
    )
