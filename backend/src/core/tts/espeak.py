"""Offline classroom voice: espeak-ng synthesizing Latin American Spanish.

Formant synthesizer: zero model weights, ~10 MB RAM, sub-second synthesis.
Writes RIFF/WAVE stream to stdout for classroom audio playback.
"""

import logging
import shutil
import subprocess

from core.config import get_settings
from core.tts.text import normalize_for_speech

__all__ = [
    "EspeakBackend",
    "TTSSynthesisError",
    "TTSUnavailableError",
    "resolve_binary",
    "resolve_voice",
    "synthesize_wav",
]

logger = logging.getLogger(__name__)

BINARY_CANDIDATES: tuple[str, ...] = ("espeak-ng", "espeak")
VOICE_FALLBACKS: dict[str, tuple[str, ...]] = {
    "es-419": ("es-la", "es-419-latin", "es"),
    "es-la": ("es-419", "es"),
}
_VOICE_LIST_TIMEOUT_SECONDS: float = 5.0


class TTSUnavailableError(RuntimeError):
    """espeak is disabled, not installed, or has no voice for the language."""


class TTSSynthesisError(RuntimeError):
    """espeak was found and ran, but produced no audio."""


def resolve_binary(configured: str = "") -> str:
    """Returns the espeak executable path, preferring espeak-ng over legacy espeak."""
    for candidate in (configured,) if configured else BINARY_CANDIDATES:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    candidates_str = configured or ", ".join(BINARY_CANDIDATES)
    raise TTSUnavailableError(
        f"espeak is not installed (looked for: {candidates_str}). "
        "Install it with: sudo apt install espeak-ng"
    )


def _installed_voices(binary: str) -> set[str]:
    """Voice identifiers espeak reports, empty when the listing cannot be read."""
    try:
        listing = subprocess.run(
            [binary, "--voices"],
            capture_output=True,
            timeout=_VOICE_LIST_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as err:
        logger.warning("Could not list espeak voices: %s", err)
        return set()
    voices: set[str] = set()
    for line in listing.stdout.decode("utf-8", errors="replace").splitlines()[1:]:
        columns = line.split()
        if len(columns) >= 2:
            voices.add(columns[1])
    return voices


def resolve_voice(binary: str, requested: str) -> str:
    """Picks the requested voice, or the closest installed Spanish fallback."""
    installed = _installed_voices(binary)
    if not installed:
        return requested
    for candidate in (requested, *VOICE_FALLBACKS.get(requested, ())):
        if candidate in installed:
            if candidate != requested:
                logger.info(
                    "espeak voice '%s' missing; using '%s'", requested, candidate
                )
            return candidate
    raise TTSUnavailableError(
        f"espeak has no voice for '{requested}'. Installed: "
        f"{', '.join(sorted(installed)[:12])}"
    )


def synthesize_wav(text: str, voice: str | None = None) -> bytes:
    """Synthesizes spoken WAV audio for the given text, raising when espeak cannot run."""
    settings = get_settings().tts
    if not settings.enabled:
        raise TTSUnavailableError("Speech synthesis is disabled (TTS_ENABLED=false).")

    spoken_text = normalize_for_speech(text, max_chars=settings.max_chars)
    if not spoken_text:
        raise TTSSynthesisError("There is no text to speak.")

    binary = resolve_binary(settings.binary)
    v = resolve_voice(binary, voice or settings.voice)
    s, p, a = (
        str(settings.words_per_minute),
        str(settings.pitch),
        str(settings.amplitude),
    )
    command = [binary, "-v", v, "-s", s, "-p", p, "-a", a, "--stdout"]
    try:
        result = subprocess.run(
            command,
            input=spoken_text.encode("utf-8"),
            capture_output=True,
            timeout=settings.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as err:
        raise TTSSynthesisError(
            f"espeak timed out after {settings.timeout_seconds}s."
        ) from err
    except OSError as err:
        raise TTSUnavailableError(f"espeak could not be executed: {err}") from err

    if result.returncode != 0 or not result.stdout:
        detail = result.stderr.decode("utf-8", errors="replace").strip()[:200]
        msg = f"espeak exited with code {result.returncode}: {detail or 'no audio'}"
        raise TTSSynthesisError(msg)
    return result.stdout


class EspeakBackend:
    """Formant speech synthesis backend conforming to TTSBackend protocol."""

    def is_available(self, voice: str | None = None) -> bool:
        """Returns True if espeak is installed and enabled."""
        settings = get_settings().tts
        if not settings.enabled:
            return False
        try:
            binary = resolve_binary(settings.binary)
            if voice:
                resolve_voice(binary, voice)
            return True
        except TTSUnavailableError:
            return False

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Synthesizes text using espeak-ng formant synthesis."""
        return synthesize_wav(text, voice=voice)
