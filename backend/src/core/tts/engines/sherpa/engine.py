"""Sherpa-ONNX speech synthesis backend for TutorBox."""

import gc
import logging
import sys
import time
from pathlib import Path
from typing import Any

from core.config import get_settings
from core.tts.constants import MILLISECONDS_PER_SECOND
from core.tts.engines.provider import resolve_execution_provider
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

        if sys.platform == "win32":
            try:
                import onnxruntime

                ort_capi = Path(onnxruntime.__file__).parent / "capi"
                if ort_capi.is_dir():
                    import os

                    os.add_dll_directory(str(ort_capi))
            except (ImportError, OSError, AttributeError) as err:
                logger.debug("Could not register onnxruntime DLL directory: %s", err)

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
        provider = resolve_execution_provider(tts_cfg.sherpa_provider)
        try:
            model_config = sherpa_onnx.OfflineTtsModelConfig(
                vits=vits_cfg,
                num_threads=tts_cfg.sherpa_threads,
                provider=provider,
            )
            self._tts = sherpa_onnx.OfflineTts(
                sherpa_onnx.OfflineTtsConfig(model=model_config)
            )
            self._current_model = model_name
        except Exception as err:
            if provider == "cuda":
                logger.info(
                    "Sherpa CUDA init unavailable; falling back to CPU: %s", err
                )
                try:
                    model_config = sherpa_onnx.OfflineTtsModelConfig(
                        vits=vits_cfg,
                        num_threads=tts_cfg.sherpa_threads,
                        provider="cpu",
                    )
                    self._tts = sherpa_onnx.OfflineTts(
                        sherpa_onnx.OfflineTtsConfig(model=model_config)
                    )
                    self._current_model = model_name
                except Exception as cpu_err:
                    raise TTSUnavailableError(
                        f"Failed to initialize Sherpa-ONNX on CPU: {cpu_err}"
                    ) from cpu_err
            else:
                raise TTSUnavailableError(
                    f"Failed to initialize Sherpa-ONNX: {err}"
                ) from err

        return (time.perf_counter() - start_time) * MILLISECONDS_PER_SECOND

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

        if not audio or not audio.samples:
            raise TTSSynthesisError("Sherpa engine produced zero audio samples.")

        return samples_to_wav(audio.samples, audio.sample_rate)
