"""Subprocess execution wrapper for espeak-ng / espeak CLI."""

import logging
import shutil
import subprocess

from core.config import get_settings
from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError
from core.tts.text import normalize_for_speech

__all__ = [
    "BINARY_CANDIDATES",
    "VOICE_FALLBACKS",
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


def resolve_binary(configured: str = "") -> str:
    """Returns espeak executable path, preferring espeak-ng over legacy espeak."""
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
    """Voice identifiers espeak reports, empty when listing cannot be read."""
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
    """Picks requested voice, or the closest installed Spanish fallback."""
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
    """Synthesizes spoken WAV audio for text, raising when espeak cannot run."""
    settings = get_settings().tts
    if not settings.enabled:
        raise TTSUnavailableError("Speech synthesis is disabled (TTS_ENABLED=false).")

    spoken_text = normalize_for_speech(text, max_chars=settings.max_chars)
    if not spoken_text:
        raise TTSSynthesisError("There is no text to speak.")

    binary = resolve_binary(settings.binary)
    target_voice = resolve_voice(binary, voice or settings.voice)
    command = [
        binary,
        "-v",
        target_voice,
        "-s",
        str(settings.words_per_minute),
        "-p",
        str(settings.pitch),
        "-a",
        str(settings.amplitude),
        "--stdout",
    ]
    try:
        res = subprocess.run(
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

    if res.returncode != 0 or not res.stdout:
        detail = res.stderr.decode("utf-8", errors="replace").strip()[:200]
        raise TTSSynthesisError(
            f"espeak exited with code {res.returncode}: {detail or 'no audio'}"
        )
    return res.stdout
