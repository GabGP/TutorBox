"""Meta MMS-TTS voices for the Mayan languages: Kʼicheʼ (quc) and Qʼeqchiʼ (kek).

The voice argument is the language code (the router passes the request's lang).
Each voice is about 115 MB of ONNX weights on the CPU; both may be loaded.
"""

import gc
import importlib.util
import time

import numpy as np

from core.config import get_settings
from core.tts.audio import samples_to_wav
from core.tts.constants import MILLISECONDS_PER_SECOND
from core.tts.engines.mms.models import (
    MMS_CHECKPOINTS,
    MmsVoice,
    find_mms_dir,
    load_mms_voice,
)
from core.tts.engines.mms.numbers import spell_out_numbers
from core.tts.engines.mms.tokens import clause_token_ids, split_clauses
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError
from core.tts.text import normalize_for_speech

__all__ = ["CLAUSE_PAUSE_SECONDS", "MmsBackend"]

CLAUSE_PAUSE_SECONDS = 0.3


def _require_enabled() -> None:
    if not get_settings().tts.enabled:
        raise TTSUnavailableError("Speech synthesis is disabled.")


def _require_mayan(voice: str | None) -> str:
    if voice not in MMS_CHECKPOINTS:
        raise TTSUnavailableError(f"MMS has no voice for '{voice}'.")
    return voice


class MmsBackend:
    """Offline Mayan speech through MMS VITS models exported to ONNX."""

    def __init__(self) -> None:
        self._voices: dict[str, MmsVoice] = {}

    @property
    def engine_name(self) -> str:
        return "mms"

    def is_available(self, voice: str | None = None) -> bool:
        """True when speech is on, ONNX Runtime is installed and the voice exists."""
        return (
            get_settings().tts.enabled
            and voice in MMS_CHECKPOINTS
            and importlib.util.find_spec("onnxruntime") is not None
            and find_mms_dir(voice) is not None
        )

    def is_loaded(self) -> bool:
        return bool(self._voices)

    def preload(self, voice: str | None = None) -> float:
        """Loads the language's voice, returning the load time in milliseconds."""
        start_time = time.perf_counter()
        _require_enabled()
        lang = _require_mayan(voice)
        self._voices[lang] = load_mms_voice(lang)
        return (time.perf_counter() - start_time) * MILLISECONDS_PER_SECOND

    def unload(self) -> None:
        self._voices.clear()
        gc.collect()

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Speaks the text clause by clause, with a short pause between clauses."""
        _require_enabled()
        lang = _require_mayan(voice)
        spoken_text = spell_out_numbers(
            normalize_for_speech(text, max_chars=get_settings().tts.max_chars)
        )
        if lang not in self._voices:
            self.preload(voice=lang)
        mms_voice = self._voices[lang]

        clauses = [
            token_ids
            for clause in split_clauses(spoken_text)
            if (token_ids := clause_token_ids(clause, mms_voice.vocabulary))
        ]
        if not clauses:
            raise TTSSynthesisError("There is no text this voice can speak.")

        pause = np.zeros(int(mms_voice.sample_rate * CLAUSE_PAUSE_SECONDS))
        chunks: list[np.ndarray] = []
        try:
            for token_ids in clauses:
                if chunks:
                    chunks.append(pause)
                input_ids = np.asarray([token_ids], dtype=np.int64)
                waveform = mms_voice.session.run(None, {"input_ids": input_ids})[0]
                chunks.append(np.asarray(waveform, dtype=np.float32).reshape(-1))
        except Exception as err:
            raise TTSSynthesisError(f"MMS synthesis failed: {err}") from err

        return samples_to_wav(np.concatenate(chunks).tolist(), mms_voice.sample_rate)
