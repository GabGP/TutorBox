"""Spoken >51% intervention audio for the teacher's device.

The teacher's browser cannot be trusted with the pedagogical rule, so this endpoint recomputes
the tally and the decision server-side and only returns audio when a single distractor really
did take more than 51% of the class. espeak-ng synthesizes it offline on the appliance.
"""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.session.dependencies import get_session_and_current_round
from core.config import get_settings
from core.db.database import get_db
from core.db.question_repository import get_question_by_id
from core.db.vote_repository import get_votes_for_round
from core.security import AuthContext, require_roles
from core.tts import TTSSynthesisError, TTSUnavailableError, synthesize_wav
from modes.quiz.session.aggregator import compute_round_tally
from modes.quiz.session.evaluator import evaluate_turn_decision
from modes.quiz.session.models import RoundStatus
from modes.quiz.session.speech import build_intervention_script

logger = logging.getLogger(__name__)
router = APIRouter()

SpeechLanguage = Literal["es", "quc"]


def _voice_for_language(language: SpeechLanguage) -> str:
    """Maps a classroom language to an installed espeak voice."""
    tts = get_settings().tts
    voice = tts.voice if language == "es" else tts.voice_quc
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No speech voice is configured for language '{language}'.",
        )
    return voice


@router.get(
    "/{session_id}/speech",
    response_class=Response,
    responses={200: {"content": {"audio/wav": {}}, "description": "WAV audio stream"}},
)
def round_speech(
    session_id: str,
    ctx: Annotated[AuthContext, Depends(require_roles("teacher", "admin"))],
    lang: SpeechLanguage = "es",
) -> Response:
    """Synthesizes the misconception explanation for the current revealed round."""
    with get_db() as conn:
        _, current_round = get_session_and_current_round(conn, session_id)
        if current_round.status != RoundStatus.REVEALED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Round has not been revealed yet.",
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

    tally = compute_round_tally(votes, question.correct_option)
    decision = evaluate_turn_decision(tally, question.distractors)
    if not decision.should_speak:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The >51% rule did not trigger for this round ({decision.reason}).",
        )

    voice = _voice_for_language(lang)
    script = build_intervention_script(question.options, tally, decision)
    try:
        audio = synthesize_wav(script, voice=voice)
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
        "Spoke >51%% intervention for round %s (%s%% chose %s)",
        current_round.id,
        decision.dominant_percentage,
        decision.dominant_distractor,
    )
    return Response(
        content=audio,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store"},
    )
