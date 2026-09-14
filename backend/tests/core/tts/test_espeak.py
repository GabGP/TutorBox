"""Unit tests for the offline espeak voice engine (src/core/tts/espeak.py).

espeak is not installed in CI, so the binary lookup and the subprocess call are both faked;
what is asserted is the command TutorBox builds and how it degrades when the engine is absent.
"""

import subprocess

import pytest

from core.config import clear_settings_cache
from core.tts.espeak import (
    TTSSynthesisError,
    TTSUnavailableError,
    resolve_binary,
    resolve_voice,
    synthesize_wav,
)

FAKE_WAV = b"RIFF\x24\x00\x00\x00WAVEfmt "
VOICE_LISTING = (
    b"Pty Language       Age/Gender VoiceName          File         Other Languages\n"
    b" 5  es             --/M       Spanish (Spain)    roa/es\n"
    b" 5  es-419         --/M       Spanish (America)  roa/es-419\n"
    b" 5  en-us          --/M       English (America)  gmw/en-US\n"
)


@pytest.fixture(autouse=True)
def _clean_settings(monkeypatch: pytest.MonkeyPatch):
    """Keeps TTS environment overrides from leaking between tests."""
    for name in ("TTS_ENABLED", "TTS_ESPEAK_BINARY", "TTS_VOICE", "TTS_MAX_CHARS"):
        monkeypatch.delenv(name, raising=False)
    clear_settings_cache()
    yield
    clear_settings_cache()


class _FakeCompleted:
    def __init__(self, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _install_fake_espeak(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[list[str]],
    synth_result: _FakeCompleted | Exception = None,
    available: tuple[str, ...] = ("espeak-ng",),
) -> None:
    """Fakes both the binary lookup and the two subprocess calls espeak needs."""
    monkeypatch.setattr(
        "core.tts.espeak.shutil.which",
        lambda name: f"/usr/bin/{name}" if name in available else None,
    )

    def fake_run(command, **kwargs):
        calls.append(command)
        if "--voices" in command:
            return _FakeCompleted(stdout=VOICE_LISTING)
        if isinstance(synth_result, Exception):
            raise synth_result
        return synth_result or _FakeCompleted(stdout=FAKE_WAV)

    monkeypatch.setattr("core.tts.espeak.subprocess.run", fake_run)


def test_resolve_binary_prefers_espeak_ng(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies espeak-ng wins over the legacy espeak binary."""
    monkeypatch.setattr(
        "core.tts.espeak.shutil.which",
        lambda name: f"/usr/bin/{name}" if name in ("espeak-ng", "espeak") else None,
    )
    assert resolve_binary() == "/usr/bin/espeak-ng"


def test_resolve_binary_falls_back_to_legacy_espeak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies an appliance with only the old espeak still speaks."""
    monkeypatch.setattr(
        "core.tts.espeak.shutil.which",
        lambda name: "/usr/bin/espeak" if name == "espeak" else None,
    )
    assert resolve_binary() == "/usr/bin/espeak"


def test_resolve_binary_honours_configured_binary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies TTS_ESPEAK_BINARY pins the executable that is used."""
    monkeypatch.setattr(
        "core.tts.espeak.shutil.which",
        lambda name: "/opt/espeak-ng" if name == "/opt/espeak-ng" else None,
    )
    assert resolve_binary("/opt/espeak-ng") == "/opt/espeak-ng"


def test_resolve_binary_missing_explains_how_to_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies a missing engine names the apt package instead of failing opaquely."""
    monkeypatch.setattr("core.tts.espeak.shutil.which", lambda name: None)
    with pytest.raises(TTSUnavailableError, match="apt install espeak-ng"):
        resolve_binary()


def test_resolve_voice_picks_latin_american_spanish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies es-419 is used verbatim when espeak reports it."""
    _install_fake_espeak(monkeypatch, [])
    assert resolve_voice("/usr/bin/espeak-ng", "es-419") == "es-419"


def test_resolve_voice_falls_back_to_castilian_when_es_419_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies an espeak build without es-419 still speaks Spanish."""

    def fake_run(command, **kwargs):
        return _FakeCompleted(
            stdout=b"Pty Language Age/Gender VoiceName File\n 5  es  --/M  Spanish  roa/es\n"
        )

    monkeypatch.setattr("core.tts.espeak.subprocess.run", fake_run)
    assert resolve_voice("/usr/bin/espeak-ng", "es-419") == "es"


def test_resolve_voice_trusts_config_when_listing_unreadable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies an unreadable voice listing does not block synthesis."""

    def fake_run(command, **kwargs):
        raise OSError("cannot list voices")

    monkeypatch.setattr("core.tts.espeak.subprocess.run", fake_run)
    assert resolve_voice("/usr/bin/espeak-ng", "es-419") == "es-419"


def test_resolve_voice_without_any_spanish_voice_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies a build with no Spanish voice reports what it does have."""

    def fake_run(command, **kwargs):
        return _FakeCompleted(
            stdout=b"Pty Language Age/Gender VoiceName File\n 5  en-us  --/M  English  gmw/en-US\n"
        )

    monkeypatch.setattr("core.tts.espeak.subprocess.run", fake_run)
    with pytest.raises(TTSUnavailableError, match="en-us"):
        resolve_voice("/usr/bin/espeak-ng", "es-419")


def test_synthesize_builds_the_latin_american_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies the voice, cadence and stdout streaming flags reach espeak."""
    calls: list[list[str]] = []
    _install_fake_espeak(monkeypatch, calls)

    audio = synthesize_wav("Dividiste 6/8 mal.")

    assert audio == FAKE_WAV
    command = calls[-1]
    assert command[0] == "/usr/bin/espeak-ng"
    assert command[command.index("-v") + 1] == "es-419"
    assert command[command.index("-s") + 1] == "150"
    assert "--stdout" in command


def test_synthesize_sends_normalized_text_on_stdin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies the spoken text is normalized and passed over stdin, not argv."""
    captured: dict[str, bytes] = {}

    monkeypatch.setattr("core.tts.espeak.shutil.which", lambda name: f"/usr/bin/{name}")

    def fake_run(command, **kwargs):
        if "--voices" in command:
            return _FakeCompleted(stdout=VOICE_LISTING)
        captured["input"] = kwargs["input"]
        return _FakeCompleted(stdout=FAKE_WAV)

    monkeypatch.setattr("core.tts.espeak.subprocess.run", fake_run)
    synthesize_wav("6/8 es igual a 3/4")

    assert captured["input"].decode("utf-8") == "6 octavos es igual a 3 cuartos"


def test_synthesize_respects_requested_voice(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies an explicit voice argument overrides the configured default."""
    calls: list[list[str]] = []
    _install_fake_espeak(monkeypatch, calls)

    synthesize_wav("Hola grupo.", voice="es")

    assert calls[-1][calls[-1].index("-v") + 1] == "es"


def test_synthesize_disabled_by_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies TTS_ENABLED=false keeps the classroom silent."""
    monkeypatch.setenv("TTS_ENABLED", "false")
    clear_settings_cache()
    with pytest.raises(TTSUnavailableError, match="disabled"):
        synthesize_wav("Hola grupo.")


def test_synthesize_rejects_empty_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies blank explanations never reach the engine."""
    _install_fake_espeak(monkeypatch, [])
    with pytest.raises(TTSSynthesisError, match="no text"):
        synthesize_wav("   ")


def test_synthesize_reports_engine_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies a non-zero espeak exit surfaces its stderr."""
    _install_fake_espeak(
        monkeypatch,
        [],
        synth_result=_FakeCompleted(stderr=b"unknown voice", returncode=1),
    )
    with pytest.raises(TTSSynthesisError, match="unknown voice"):
        synthesize_wav("Hola grupo.")


def test_synthesize_reports_empty_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies a successful exit with no audio is still an error."""
    _install_fake_espeak(monkeypatch, [], synth_result=_FakeCompleted(stdout=b""))
    with pytest.raises(TTSSynthesisError, match="no audio produced"):
        synthesize_wav("Hola grupo.")


def test_synthesize_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies a hung engine cannot stall the reveal screen forever."""
    _install_fake_espeak(
        monkeypatch,
        [],
        synth_result=subprocess.TimeoutExpired(cmd="espeak-ng", timeout=10.0),
    )
    with pytest.raises(TTSSynthesisError, match="timed out"):
        synthesize_wav("Hola grupo.")


def test_synthesize_reports_unexecutable_binary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies an espeak that cannot be executed is reported as unavailable."""
    _install_fake_espeak(monkeypatch, [], synth_result=OSError("permission denied"))
    with pytest.raises(TTSUnavailableError, match="could not be executed"):
        synthesize_wav("Hola grupo.")
