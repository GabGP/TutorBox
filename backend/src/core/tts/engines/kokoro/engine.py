"""Kokoro-82M neural speech synthesis backend leveraging Sherpa-ONNX runtime."""

import gc
import logging
import time
from typing import Any

from core.config import get_settings
from core.tts.constants import DEFAULT_SPEECH_SPEED, MILLISECONDS_PER_SECOND
from core.tts.engines.kokoro.models import (
    resolve_kokoro_paths,
    resolve_speaker_id,
    samples_to_wav,
)
from core.tts.engines.provider import resolve_execution_provider
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError
from core.tts.text import normalize_for_speech

__all__ = ["KokoroBackend"]

logger = logging.getLogger(__name__)


class KokoroBackend:
    """Offline Kokoro-82M neural synthesis backend running via sherpa-onnx."""

    def __init__(self) -> None:
        self._tts: Any | None = None
        self._current_model_dir: str | None = None

    @property
    def engine_name(self) -> str:
        return "kokoro"

    def is_available(self, voice: str | None = None) -> bool:
        """Returns True if sherpa-onnx runtime and Kokoro weights are present."""
        tts = get_settings().tts
        if not tts.enabled:
            return False
        try:
            import sherpa_onnx  # noqa: F401
        except ImportError:
            return False

        try:
            resolve_kokoro_paths()
            return True
        except TTSUnavailableError:
            return False

    def is_loaded(self) -> bool:
        """Returns True if the Kokoro engine is initialized in memory."""
        return self._tts is not None

    def preload(self, voice: str | None = None) -> float:
        """Initializes Kokoro model weights into memory, returning load duration in ms."""
        start_time = time.perf_counter()
        tts_cfg = get_settings().tts
        if not tts_cfg.enabled:
            raise TTSUnavailableError("Speech synthesis is disabled.")

        try:
            import sherpa_onnx
        except ImportError as err:
            raise TTSUnavailableError("sherpa-onnx runtime is not installed.") from err

        paths = resolve_kokoro_paths()
        lexicon_str = ",".join(str(p) for p in paths.lexicon_paths)
        dict_str = str(paths.dict_dir) if paths.dict_dir else ""

        k_cfg = sherpa_onnx.OfflineTtsKokoroModelConfig(
            model=str(paths.model_path),
            voices=str(paths.voices_path),
            tokens=str(paths.tokens_path),
            data_dir=str(paths.data_dir),
            dict_dir=dict_str,
            lexicon=lexicon_str,
            lang=tts_cfg.kokoro_voice,
        )
        provider = resolve_execution_provider(tts_cfg.kokoro_provider)
        try:
            model_config = sherpa_onnx.OfflineTtsModelConfig(
                kokoro=k_cfg,
                num_threads=tts_cfg.sherpa_threads,
                provider=provider,
            )
            self._tts = sherpa_onnx.OfflineTts(
                sherpa_onnx.OfflineTtsConfig(model=model_config)
            )
            self._current_model_dir = str(paths.model_path.parent)
        except Exception as err:
            if provider == "cuda":
                logger.info("Kokoro CUDA init failed; falling back to CPU: %s", err)
                model_config = sherpa_onnx.OfflineTtsModelConfig(
                    kokoro=k_cfg,
                    num_threads=tts_cfg.sherpa_threads,
                    provider="cpu",
                )
                self._tts = sherpa_onnx.OfflineTts(
                    sherpa_onnx.OfflineTtsConfig(model=model_config)
                )
                self._current_model_dir = str(paths.model_path.parent)
            else:
                raise TTSUnavailableError(
                    f"Failed to initialize Kokoro: {err}"
                ) from err

        return (time.perf_counter() - start_time) * MILLISECONDS_PER_SECOND

    def unload(self) -> None:
        """Reclaims memory by releasing the Kokoro engine instance."""
        self._tts = None
        self._current_model_dir = None
        gc.collect()

    def _resolve_speaker_id(self, voice: str | None) -> int:
        return resolve_speaker_id(voice, get_settings().tts.kokoro_speaker_id)

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Synthesizes text into calibrated 24 kHz WAV audio bytes using Kokoro."""
        tts_cfg = get_settings().tts
        if not tts_cfg.enabled:
            raise TTSUnavailableError("Speech synthesis is disabled.")
        spoken_text = normalize_for_speech(text, max_chars=tts_cfg.max_chars)
        if not spoken_text:
            raise TTSSynthesisError("There is no text to speak.")

        if self._tts is None:
            self.preload(voice=voice)

        if self._tts is None:
            raise TTSUnavailableError("Kokoro engine is not initialized.")

        speaker_id = self._resolve_speaker_id(voice)
        try:
            audio = self._tts.generate(
                spoken_text, sid=speaker_id, speed=DEFAULT_SPEECH_SPEED
            )
        except Exception as err:
            raise TTSSynthesisError(f"Kokoro synthesis failed: {err}") from err

        if not audio or not audio.samples:
            raise TTSSynthesisError("Kokoro engine produced zero audio samples.")

        return samples_to_wav(audio.samples, audio.sample_rate)
