"""Qwen3-TTS neural speech synthesis backend via llama-tts daemon."""

import gc
import logging
import tempfile
import time
from pathlib import Path

from core.config import get_settings
from core.tts.audio import calibrate_wav_peak
from core.tts.constants import MILLISECONDS_PER_SECOND
from core.tts.engines.qwen.daemon import QwenDaemonClient
from core.tts.engines.qwen.models import QwenModelPaths, resolve_qwen_paths
from core.tts.engines.qwen.runner import (
    build_qwen_daemon_command,
    execute_qwen_cli,
    parse_qwen_timings,
)
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError
from core.tts.text import normalize_for_speech

__all__ = ["QwenBackend"]
logger = logging.getLogger(__name__)


def _speaker_path(configured_speaker: str) -> Path | None:
    if not configured_speaker:
        return None
    path = Path(configured_speaker).expanduser()
    if not path.is_file():
        raise TTSUnavailableError(f"Qwen speaker file not found at '{path}'.")
    return path


class QwenBackend:
    """Offline Qwen3-TTS Base synthesis backend running via persistent daemon."""

    def __init__(self) -> None:
        self._loaded = False
        self._paths: QwenModelPaths | None = None
        self._daemon_client: QwenDaemonClient | None = None
        self._last_timings: dict[str, float] = {}
        self._last_synthesis_seconds: float | None = None

    @property
    def engine_name(self) -> str:
        return "qwen3-tts"

    def is_available(self, voice: str | None = None) -> bool:
        if not get_settings().tts.enabled:
            return False
        try:
            return resolve_qwen_paths() is not None
        except TTSUnavailableError:
            return False

    def is_loaded(self) -> bool:
        return self._daemon_client.is_alive() if self._daemon_client else self._loaded

    @property
    def last_synthesis_seconds(self) -> float | None:
        return self._last_synthesis_seconds

    @property
    def last_timings(self) -> dict[str, float]:
        return dict(self._last_timings)

    def preload(self, voice: str | None = None) -> float:
        start = time.perf_counter()
        tts = get_settings().tts
        if not tts.enabled:
            raise TTSUnavailableError("Speech synthesis is disabled.")
        self._paths = resolve_qwen_paths()
        if self._paths.daemon_bin_path and not self.is_loaded():
            spk = _speaker_path(tts.qwen_speaker_file)
            cmd = build_qwen_daemon_command(self._paths, tts, speaker_file=spk)
            try:
                self._daemon_client = QwenDaemonClient(
                    cmd, startup_timeout=tts.timeout_seconds
                )
            except TTSUnavailableError as err:
                logger.warning("Daemon unavailable, using CLI fallback: %s", err)
                self._daemon_client = None
        self._loaded = True
        return (time.perf_counter() - start) * MILLISECONDS_PER_SECOND

    def unload(self) -> None:
        if self._daemon_client:
            self._daemon_client.close()
        self._daemon_client, self._loaded, self._paths = None, False, None
        self._last_timings, self._last_synthesis_seconds = {}, None
        gc.collect()

    def _execute_cli(
        self, p: QwenModelPaths, txt: str, lang: str, wav: Path, spk: Path | None
    ) -> str:
        return execute_qwen_cli(p, txt, lang, wav, get_settings().tts, speaker_file=spk)

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        tts = get_settings().tts
        if not tts.enabled:
            raise TTSUnavailableError("Speech synthesis is disabled.")
        spoken = normalize_for_speech(text, max_chars=tts.max_chars)
        if not spoken:
            raise TTSSynthesisError("There is no text to speak.")

        paths = self._paths or resolve_qwen_paths()
        self._paths, lang = paths, voice if voice and len(voice) == 2 else "es"
        if not self.is_loaded() and paths.daemon_bin_path:
            self.preload(voice=lang)
        spk = _speaker_path(tts.qwen_speaker_file)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_wav = Path(tmp.name)
        try:
            if self._daemon_client and self._daemon_client.is_alive():
                raw = self._daemon_client.synthesize(
                    lang, tmp_wav, spoken, timeout_seconds=tts.timeout_seconds
                )
            else:
                raw = self._execute_cli(paths, spoken, lang, tmp_wav, spk)
            wav_bytes = tmp_wav.read_bytes() if tmp_wav.exists() else b""
            if not wav_bytes:
                raise TTSSynthesisError("Qwen engine produced zero audio bytes.")
            self._last_timings = parse_qwen_timings(raw)
            self._last_synthesis_seconds = self._last_timings.get("synthesis_s")
            self._loaded = True
            return calibrate_wav_peak(wav_bytes)
        except (TTSSynthesisError, TTSUnavailableError):
            raise
        except Exception as err:
            raise TTSSynthesisError(f"Qwen synthesis error: {err}") from err
        finally:
            tmp_wav.unlink(missing_ok=True)
