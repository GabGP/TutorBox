"""Sherpa-ONNX speech synthesis backend for TutorBox."""

import gc
import logging
import time
from typing import Any

from core.config import get_settings
from core.tts.engines.sherpa.models import resolve_sherpa_paths, samples_to_wav
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError
from core.tts.text import normalize_for_speech

__all__ = ["SherpaBackend"]

logger = logging.getLogger(__name__)


class SherpaBackend:
    """Offline neural synthesis backend leveraging sherpa-onnx runtime."""

    def __init__(self) -> None:
        self._tts: Any | None = None
        self._current_model: str | None = None

    @property
    def engine_name(self) -> str:
        return "sherpa"

    def _resolve_model(self, voice: str | None) -> str:
        tts = get_settings().tts
        return tts.sherpa_model_es if voice in (None, "es") else voice

    def is_available(self, voice: str | None = None) -> bool:
        """Returns True if sherpa-onnx is installed and model files are present."""
        tts = get_settings().tts
        if not tts.enabled:
            return False
        try:
            import sherpa_onnx  # noqa: F401
        except ImportError:
            return False

        model_name = self._resolve_model(voice)
        try:
            resolve_sherpa_paths(model_name)
            return True
        except TTSUnavailableError:
            return False

    def is_loaded(self) -> bool:
        """Returns True if the sherpa-onnx TTS engine is initialized in memory."""
        return self._tts is not None

    def preload(self, voice: str | None = None) -> float:
        """Initializes sherpa-onnx model weights into memory, returning load duration in ms."""
        start_time = time.perf_counter()
        tts_cfg = get_settings().tts
        if not tts_cfg.enabled:
            raise TTSUnavailableError("Speech synthesis is disabled.")

        try:
            import sherpa_onnx
        except ImportError as err:
            raise TTSUnavailableError("sherpa-onnx runtime is not installed.") from err

        model_name = self._resolve_model(voice)
        model_path, tokens_path, data_dir = resolve_sherpa_paths(model_name)

        vits_cfg = sherpa_onnx.OfflineTtsVitsModelConfig(
            model=str(model_path),
            tokens=str(tokens_path),
            data_dir=str(data_dir),
            length_scale=tts_cfg.piper_length_scale,
            noise_scale=tts_cfg.piper_noise_scale,
            noise_scale_w=tts_cfg.piper_noise_w_scale,
        )
        model_config = sherpa_onnx.OfflineTtsModelConfig(
            vits=vits_cfg,
            num_threads=tts_cfg.sherpa_threads,
        )
        engine_config = sherpa_onnx.OfflineTtsConfig(model=model_config)
        try:
            self._tts = sherpa_onnx.OfflineTts(engine_config)
            self._current_model = model_name
        except Exception as err:
            raise TTSUnavailableError(
                f"Failed to initialize Sherpa-ONNX: {err}"
            ) from err

        return (time.perf_counter() - start_time) * 1000.0

    def unload(self) -> None:
        """Reclaims memory by releasing the sherpa-onnx engine instance."""
        self._tts = None
        self._current_model = None
        gc.collect()

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Synthesizes text into standard WAV audio bytes using Sherpa-ONNX."""
        tts_cfg = get_settings().tts
        if not tts_cfg.enabled:
            raise TTSUnavailableError("Speech synthesis is disabled.")
        spoken_text = normalize_for_speech(text, max_chars=tts_cfg.max_chars)
        if not spoken_text:
            raise TTSSynthesisError("There is no text to speak.")

        target_model = self._resolve_model(voice)
        if self._tts is None or self._current_model != target_model:
            self.preload(voice=target_model)

        if self._tts is None:
            raise TTSUnavailableError("Sherpa engine is not initialized.")

        speaker_id = tts_cfg.piper_speaker_es
        try:
            audio = self._tts.generate(spoken_text, sid=speaker_id)
        except Exception as err:
            raise TTSSynthesisError(f"Sherpa synthesis failed: {err}") from err

        if not audio or len(audio.samples) == 0:
            raise TTSSynthesisError("Sherpa engine produced zero audio samples.")

        return samples_to_wav(audio.samples, audio.sample_rate)
