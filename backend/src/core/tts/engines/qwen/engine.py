"""Qwen3-TTS neural speech synthesis backend via llama-tts."""

import gc
import logging
import subprocess
import tempfile
import time
from pathlib import Path

from core.config import get_settings
from core.tts.audio import calibrate_wav_peak
from core.tts.constants import (
    MILLISECONDS_PER_SECOND,
    SUBPROCESS_SUCCESS_EXIT_CODE,
)
from core.tts.engines.qwen.models import QwenModelPaths, resolve_qwen_paths
from core.tts.engines.qwen.runner import (
    build_qwen_command,
    parse_qwen_timings,
)
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError
from core.tts.text import normalize_for_speech

__all__ = ["QwenBackend"]

logger = logging.getLogger(__name__)


class QwenBackend:
    """Offline Qwen3-TTS Base synthesis backend running via llama-tts."""

    def __init__(self) -> None:
        self._loaded: bool = False
        self._paths: QwenModelPaths | None = None
        self._last_timings: dict[str, float] = {}
        self._last_synthesis_seconds: float | None = None

    @property
    def engine_name(self) -> str:
        return "qwen3-tts"

    def is_available(self, voice: str | None = None) -> bool:
        """Returns True if Qwen3-TTS model weights and executor binary are present."""
        tts = get_settings().tts
        if not tts.enabled:
            return False
        try:
            resolve_qwen_paths()
            return True
        except TTSUnavailableError:
            return False

    def is_loaded(self) -> bool:
        """Returns True if the Qwen backend has been initialized."""
        return self._loaded

    @property
    def last_synthesis_seconds(self) -> float | None:
        """Returns the pure neural synthesis duration from the last run, if available."""
        return self._last_synthesis_seconds

    @property
    def last_timings(self) -> dict[str, float]:
        """Returns the parsed internal timings dict from the last synthesis run."""
        return dict(self._last_timings)

    def preload(self, voice: str | None = None) -> float:
        """Verifies model and binary availability, returning check duration in ms."""
        start_time = time.perf_counter()
        tts_cfg = get_settings().tts
        if not tts_cfg.enabled:
            raise TTSUnavailableError("Speech synthesis is disabled.")
        self._paths = resolve_qwen_paths()
        self._loaded = True
        return (time.perf_counter() - start_time) * MILLISECONDS_PER_SECOND

    def unload(self) -> None:
        """Reclaims memory state for the Qwen backend."""
        self._loaded = False
        self._paths = None
        self._last_timings = {}
        self._last_synthesis_seconds = None
        gc.collect()

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Synthesizes 24 kHz WAV audio; llama-tts selects CUDA when available."""
        tts_cfg = get_settings().tts
        if not tts_cfg.enabled:
            raise TTSUnavailableError("Speech synthesis is disabled.")
        spoken_text = normalize_for_speech(text, max_chars=tts_cfg.max_chars)
        if not spoken_text:
            raise TTSSynthesisError("There is no text to speak.")

        paths = self._paths or resolve_qwen_paths()
        self._paths = paths
        lang = voice if voice and len(voice) == 2 else "es"
        speaker_file = (
            Path(tts_cfg.qwen_speaker_file).expanduser()
            if tts_cfg.qwen_speaker_file
            else None
        )
        if speaker_file and not speaker_file.is_file():
            raise TTSUnavailableError(
                f"Qwen speaker file not found at '{speaker_file}'."
            )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_wav = Path(tmp_file.name)

        try:
            cmd = build_qwen_command(
                paths,
                spoken_text,
                lang,
                tmp_wav,
                tts_cfg,
                speaker_file=speaker_file,
            )
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=tts_cfg.timeout_seconds,
                check=False,
            )
            if res.returncode != SUBPROCESS_SUCCESS_EXIT_CODE or not tmp_wav.exists():
                raise TTSSynthesisError(f"Qwen synthesis failed: {res.stdout}")
            wav_bytes = tmp_wav.read_bytes()
            if not wav_bytes:
                raise TTSSynthesisError("Qwen engine produced zero audio bytes.")
            self._last_timings = parse_qwen_timings(res.stdout)
            self._last_synthesis_seconds = self._last_timings.get("synthesis_s")
            self._loaded = True
            return calibrate_wav_peak(wav_bytes)
        except subprocess.TimeoutExpired as err:
            raise TTSSynthesisError(
                f"Qwen synthesis timed out after {tts_cfg.timeout_seconds}s."
            ) from err
        except Exception as err:
            if isinstance(err, (TTSSynthesisError, TTSUnavailableError)):
                raise
            raise TTSSynthesisError(f"Qwen synthesis encountered error: {err}") from err
        finally:
            if tmp_wav.exists():
                tmp_wav.unlink(missing_ok=True)
