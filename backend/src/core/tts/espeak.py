"""Offline classroom voice: espeak-ng synthesizing Latin American Spanish on the appliance.

espeak-ng is a formant synthesizer: no model files, ~10 MB of RAM and well under the 3 s
synthesis budget on the Jetson, which is what keeps the >51% intervention instant and offline.
The engine writes a RIFF/WAVE stream to stdout; the teacher's browser plays those bytes.
"""

import logging
import shutil
import subprocess

from core.config import get_settings
from core.tts.text import normalize_for_speech

__all__ = [
    "TTSSynthesisError",
    "TTSUnavailableError",
    "resolve_binary",
    "resolve_voice",
    "synthesize_wav",
]

logger = logging.getLogger(__name__)

BINARY_CANDIDATES: tuple[str, ...] = ("espeak-ng", "espeak")
# es-419 is espeak-ng's Latin American Spanish; legacy espeak ships the same voice as es-la,
# and plain es (Castilian) is the last resort so a class still hears the explanation.
VOICE_FALLBACKS: dict[str, tuple[str, ...]] = {
    "es-419": ("es-la", "es-419-latin", "es"),
    "es-la": ("es-419", "es"),
}
_VOICE_LIST_TIMEOUT_SECONDS: float = 5.0


class TTSUnavailableError(RuntimeError):
    """espeak is disabled, not installed, or has no voice for the requested language."""


class TTSSynthesisError(RuntimeError):
    """espeak was found and ran, but produced no audio."""


def resolve_binary(configured: str = "") -> str:
    """Returns the espeak executable path, preferring espeak-ng over legacy espeak."""
    for candidate in (configured,) if configured else BINARY_CANDIDATES:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise TTSUnavailableError(
        f"espeak is not installed on this appliance (looked for: "
        f"{configured or ', '.join(BINARY_CANDIDATES)}). Install it with: "
        f"sudo apt install espeak-ng"
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
    # Columns: Pty Language Age/Gender VoiceName File Other Languages
    voices: set[str] = set()
    for line in listing.stdout.decode("utf-8", errors="replace").splitlines()[1:]:
        columns = line.split()
        if len(columns) >= 2:
            voices.add(columns[1])
    return voices


def resolve_voice(binary: str, requested: str) -> str:
    """Picks the requested voice, or the closest installed Spanish fallback."""
    installed = _installed_voices(binary)
    # An unreadable listing must not block a class: trust the configuration and let espeak decide.
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
        f"espeak has no voice for '{requested}'. Installed voices: "
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
    command = [
        binary,
        "-v",
        resolve_voice(binary, voice or settings.voice),
        "-s",
        str(settings.words_per_minute),
        "-p",
        str(settings.pitch),
        "-a",
        str(settings.amplitude),
        "--stdout",
    ]
    try:
        # Text goes over stdin: no argv length limit and no quoting surprises.
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
        raise TTSSynthesisError(
            f"espeak exited with code {result.returncode}: {detail or 'no audio produced'}"
        )
    return result.stdout
