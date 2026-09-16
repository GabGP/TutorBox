"""Neural Piper VITS speech synthesis backend for TutorBox."""

import gc
import io
import logging
import shutil
import subprocess
import time
import wave
from pathlib import Path
from typing import Any

from core.config import get_settings
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError
from core.tts.piper_models import resolve_model_path, sanitize_model_config
from core.tts.text import normalize_for_speech

__all__ = ["PiperBackend", "resolve_model_path", "sanitize_model_config"]

logger = logging.getLogger(__name__)
_VOICE_CACHE: dict[str, Any] = {}


class PiperBackend:
    """Synthesizes high-fidelity speech using Piper-TTS VITS models."""

    @property
    def engine_name(self) -> str:
        return "piper"

    def _resolve_voice_and_speaker(self, voice: str | None) -> tuple[str, int]:
        tts = get_settings().tts
        if voice == "quc":
            return tts.piper_model_quc, tts.piper_speaker_quc
        return tts.piper_model_es, tts.piper_speaker_es

    def is_available(self, voice: str | None = None) -> bool:
        """Returns True if the requested model and inference engine are present."""
        tts = get_settings().tts
        if not tts.enabled:
            return False
        model_name, _ = self._resolve_voice_and_speaker(voice)
        try:
            resolve_model_path(model_name, tts.piper_model_dir)
            return True
        except TTSUnavailableError:
            return False

    def is_loaded(self) -> bool:
        """Returns True if any Piper voice is currently cached in memory."""
        return bool(_VOICE_CACHE)

    def preload(self, voice: str | None = None) -> float:
        """Preloads Piper voice into memory cache, returning load duration in ms."""
        start_time = time.perf_counter()
        tts = get_settings().tts
        if not tts.enabled:
            raise TTSUnavailableError("Speech synthesis is disabled.")
        model_name, _ = self._resolve_voice_and_speaker(voice)
        model_path = resolve_model_path(model_name, tts.piper_model_dir)
        cache_key = str(model_path)
        if cache_key not in _VOICE_CACHE:
            from piper.voice import PiperVoice

            config_path = model_path.with_suffix(".onnx.json")
            sanitize_model_config(config_path)
            _VOICE_CACHE[cache_key] = PiperVoice.load(
                str(model_path), config_path=str(config_path)
            )
        return (time.perf_counter() - start_time) * 1000.0

    def unload(self) -> None:
        """Unloads cached voices from memory."""
        _VOICE_CACHE.clear()
        gc.collect()

    def _synthesize_in_memory(
        self, model_path: Path, text: str, speaker_id: int
    ) -> bytes:
        from piper.config import SynthesisConfig
        from piper.voice import PiperVoice

        config_path = model_path.with_suffix(".onnx.json")
        sanitize_model_config(config_path)

        cache_key = str(model_path)
        if cache_key not in _VOICE_CACHE:
            _VOICE_CACHE[cache_key] = PiperVoice.load(
                str(model_path), config_path=str(config_path)
            )
        voice = _VOICE_CACHE[cache_key]

        tts = get_settings().tts
        syn_cfg = SynthesisConfig(
            speaker_id=speaker_id,
            length_scale=tts.piper_length_scale,
            noise_scale=tts.piper_noise_scale,
            noise_w_scale=tts.piper_noise_w_scale,
        )
        raw_pcm = bytearray()
        for chunk in voice.synthesize(text, syn_config=syn_cfg):
            raw_pcm.extend(chunk.audio_int16_bytes)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(voice.config.sample_rate)
            wav_file.writeframes(raw_pcm)
        return buf.getvalue()

    def _synthesize_subprocess(
        self, model_path: Path, text: str, speaker_id: int
    ) -> bytes:
        binary = shutil.which(get_settings().tts.piper_binary or "piper")
        if not binary:
            raise TTSUnavailableError("Piper executable is not installed.")
        cmd = [binary, "-m", str(model_path), "-s", str(speaker_id), "--output-raw"]
        res = subprocess.run(
            cmd, input=text.encode("utf-8"), capture_output=True, check=False
        )
        if res.returncode != 0 or not res.stdout:
            raise TTSSynthesisError(f"Piper exited with code {res.returncode}")
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(res.stdout)
        return buf.getvalue()

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Synthesizes spoken WAV audio for the given text using Piper VITS."""
        tts = get_settings().tts
        if not tts.enabled:
            raise TTSUnavailableError("Speech synthesis is disabled.")
        spoken_text = normalize_for_speech(text, max_chars=tts.max_chars)
        if not spoken_text:
            raise TTSSynthesisError("There is no text to speak.")

        model_name, speaker_id = self._resolve_voice_and_speaker(voice)
        model_path = resolve_model_path(model_name, tts.piper_model_dir)

        try:
            return self._synthesize_in_memory(model_path, spoken_text, speaker_id)
        except (RuntimeError, OSError, ValueError, KeyError, ImportError) as err:
            logger.info("In-memory synthesis fell back to subprocess: %s", err)
            return self._synthesize_subprocess(model_path, spoken_text, speaker_id)
