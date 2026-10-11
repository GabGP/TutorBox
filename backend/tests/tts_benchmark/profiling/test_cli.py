"""Verifies the benchmark command line: its defaults, its flags and the metric lines it prints."""

import sys

import pytest

from tools.benchmark.tts.profiling import cli
from tools.benchmark.tts.profiling.results import ProfileResult

DEFAULT_TEXT = (
    "Atención: 100 por ciento del grupo respondió un medio. "
    "Dividiste sólo el numerador entre 2. La respuesta correcta es tres cuartos."
)

SAMPLE_RESULT = ProfileResult(
    text="hola",
    latency_seconds=2.219,
    audio_duration_seconds=8.15,
    real_time_factor=0.272,
    sample_rate=22050,
    peak_amplitude=0.78,
    audio_byte_count=351 * 1024,
)


def _install_fake_profiler(monkeypatch) -> list[dict]:
    """Replaces the single-run profiler with one that returns SAMPLE_RESULT and records its arguments."""
    recorded_calls: list[dict] = []

    def fake_profile_speech_synthesis(text, lang="es", voice=None, *, engine=None):
        """Records the forwarded arguments and returns the sample result."""
        recorded_calls.append(
            {"text": text, "lang": lang, "voice": voice, "engine": engine}
        )
        return SAMPLE_RESULT

    monkeypatch.setattr(cli, "profile_speech_synthesis", fake_profile_speech_synthesis)
    return recorded_calls


def test_defaults_without_flags_or_environment(monkeypatch):
    """Verifies the engine falls back to piper and the other options to their defaults."""
    monkeypatch.delenv("TTS_ENGINE", raising=False)
    monkeypatch.setattr(sys, "argv", ["benchmark.py"])
    arguments = cli.parse_arguments()
    assert arguments.engine == "piper"
    assert arguments.text == DEFAULT_TEXT
    assert arguments.lang == "es"
    assert arguments.voice is None


def test_engine_default_comes_from_the_tts_engine_variable(monkeypatch):
    """Verifies the engine default is read from the TTS_ENGINE environment variable."""
    monkeypatch.setenv("TTS_ENGINE", "kokoro")
    monkeypatch.setattr(sys, "argv", ["benchmark.py"])
    assert cli.parse_arguments().engine == "kokoro"


def test_engine_flag_overrides_the_environment(monkeypatch):
    """Verifies an explicit --engine wins over the TTS_ENGINE environment variable."""
    monkeypatch.setenv("TTS_ENGINE", "kokoro")
    monkeypatch.setattr(sys, "argv", ["benchmark.py", "--engine", "piper"])
    assert cli.parse_arguments().engine == "piper"


def test_explicit_flags_are_parsed(monkeypatch):
    """Verifies every flag is read into its matching option."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark.py",
            "--engine",
            "sherpa",
            "--text",
            "Hola",
            "--lang",
            "en",
            "--voice",
            "amy",
        ],
    )
    arguments = cli.parse_arguments()
    assert (arguments.engine, arguments.text, arguments.lang, arguments.voice) == (
        "sherpa",
        "Hola",
        "en",
        "amy",
    )


def test_unknown_flag_is_rejected(monkeypatch):
    """Verifies an unknown flag makes argparse exit with code 2."""
    monkeypatch.setattr(sys, "argv", ["benchmark.py", "--bogus"])
    with pytest.raises(SystemExit) as exit_info:
        cli.parse_arguments()
    assert exit_info.value.code == 2


def test_main_prints_the_header_and_six_metric_lines(monkeypatch, capsys):
    """Verifies main prints the header and the six metric lines, in order, and nothing else."""
    _install_fake_profiler(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["benchmark.py", "--engine", "piper"])
    cli.main()
    assert capsys.readouterr().out.splitlines() == [
        "Benchmarking Utz'tutor Neural TTS Pipeline [piper]...",
        "Latency:      2.219 s",
        "Audio Length: 8.15 s",
        "RTF:          0.272x",
        "Sample Rate:  22050 Hz",
        "Peak Level:   0.78 (normalized)",
        "WAV Size:     351.0 KB",
    ]


def test_main_forwards_text_language_voice_and_engine(monkeypatch):
    """Verifies main passes the parsed text, language, voice and engine to the profiler."""
    recorded_calls = _install_fake_profiler(monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark.py",
            "--engine",
            "sherpa",
            "--text",
            "Hola",
            "--lang",
            "en",
            "--voice",
            "amy",
        ],
    )
    cli.main()
    assert recorded_calls == [
        {"text": "Hola", "lang": "en", "voice": "amy", "engine": "sherpa"}
    ]


def test_main_uses_the_defaults_when_no_flags_are_given(monkeypatch, capsys):
    """Verifies main forwards the default text, es, no voice and piper when given no flags."""
    monkeypatch.delenv("TTS_ENGINE", raising=False)
    recorded_calls = _install_fake_profiler(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["benchmark.py"])
    cli.main()
    assert recorded_calls == [
        {"text": DEFAULT_TEXT, "lang": "es", "voice": None, "engine": "piper"}
    ]
    assert capsys.readouterr().out.splitlines()[0] == (
        "Benchmarking Utz'tutor Neural TTS Pipeline [piper]..."
    )
