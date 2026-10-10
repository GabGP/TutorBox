"""Verifies the MeloTTS harness command line: flags, --profile output, plain synthesis and output paths."""

import sys

import pytest

from tools.benchmark.tts.melo import cli
from tools.benchmark.tts.shared import paths
from tools.benchmark.tts.shared.sample_text import DEFAULT_INTERVENTION_TEXT


def set_arguments(monkeypatch, *flags: str) -> None:
    """Sets sys.argv to the harness script name followed by the given flags."""
    monkeypatch.setattr(sys, "argv", ["harness.py", *flags])


def install_fake_profile(monkeypatch, report: dict) -> list[dict]:
    """Replaces cli.profile_melo with a function that returns report and records its arguments."""
    recorded_calls: list[dict] = []

    def fake_profile_melo(text, repeats, provider):
        recorded_calls.append({"text": text, "repeats": repeats, "provider": provider})
        return report

    monkeypatch.setattr(cli, "profile_melo", fake_profile_melo)
    return recorded_calls


def install_fake_harness(monkeypatch, wav_bytes: bytes) -> list[tuple]:
    """Replaces cli.MeloTTSHarness with a stand-in that records its calls and returns wav_bytes."""
    recorded_calls: list[tuple] = []

    class FakeMeloTTSHarness:
        """Stands in for MeloTTSHarness without loading any model."""

        def __init__(self, provider: str = "cpu") -> None:
            recorded_calls.append(("init", provider))

        def synthesize(self, text: str) -> bytes:
            recorded_calls.append(("synthesize", text))
            return wav_bytes

    monkeypatch.setattr(cli, "MeloTTSHarness", FakeMeloTTSHarness)
    return recorded_calls


def test_defaults_when_no_flags_are_given(monkeypatch):
    """Verifies a run without flags uses the default text, cpu provider and 5 repeats."""
    set_arguments(monkeypatch)
    arguments = cli.parse_arguments()
    assert arguments.text == DEFAULT_INTERVENTION_TEXT
    assert arguments.out is None
    assert arguments.repeats == 5
    assert arguments.provider == "cpu"
    assert arguments.profile is False


def test_every_flag_is_parsed(monkeypatch):
    """Verifies each flag lands in its own option, with repeats read as an integer."""
    set_arguments(
        monkeypatch,
        "--text",
        "Hola",
        "--out",
        "clip.wav",
        "--repeats",
        "3",
        "--provider",
        "cuda",
        "--profile",
    )
    arguments = cli.parse_arguments()
    assert arguments.text == "Hola"
    assert arguments.out == "clip.wav"
    assert arguments.repeats == 3
    assert arguments.provider == "cuda"
    assert arguments.profile is True


def test_unknown_provider_is_rejected_with_exit_code_two(monkeypatch):
    """Verifies a provider outside cpu and cuda makes argparse exit with code 2."""
    set_arguments(monkeypatch, "--provider", "tpu")
    with pytest.raises(SystemExit) as exit_info:
        cli.parse_arguments()
    assert exit_info.value.code == 2


def test_help_names_the_harness(monkeypatch, capsys):
    """Verifies --help exits cleanly and shows the harness description."""
    set_arguments(monkeypatch, "--help")
    with pytest.raises(SystemExit) as exit_info:
        cli.parse_arguments()
    assert exit_info.value.code == 0
    assert "MeloTTS Spanish ONNX harness" in capsys.readouterr().out


def test_profile_run_prints_each_figure_but_the_audio_and_saves_the_wav(
    monkeypatch, tmp_path, capsys
):
    """Verifies --profile prints the header and each figure except the audio, then saves the WAV."""
    out_path = tmp_path / "nested" / "clip.wav"
    report = {
        "engine": "melo",
        "provider": "cuda",
        "cold_first_s": 0.75,
        "warm_p50_s": 0.5,
        "rtf_p50": 0.25,
        "sr_hz": 22050,
        "wav_kb": 1.5,
        "wav_bytes": b"fake-wav",
    }
    install_fake_profile(monkeypatch, report)
    set_arguments(
        monkeypatch, "--profile", "--provider", "cuda", "--out", str(out_path)
    )
    assert cli.main() == 0
    assert capsys.readouterr().out.splitlines() == [
        "Profiling MeloTTS Spanish [cuda]...",
        "  engine: melo",
        "  provider: cuda",
        "  cold_first_s: 0.75",
        "  warm_p50_s: 0.5",
        "  rtf_p50: 0.25",
        "  sr_hz: 22050",
        "  wav_kb: 1.5",
        f"WAV saved to {out_path}",
    ]
    assert out_path.read_bytes() == b"fake-wav"


def test_profile_run_forwards_text_repeats_and_provider(monkeypatch, tmp_path):
    """Verifies --text, --repeats and --provider reach profile_melo unchanged."""
    recorded_calls = install_fake_profile(monkeypatch, {"wav_bytes": b""})
    set_arguments(
        monkeypatch,
        "--profile",
        "--text",
        "Hola",
        "--repeats",
        "2",
        "--provider",
        "cuda",
        "--out",
        str(tmp_path / "clip.wav"),
    )
    cli.main()
    assert recorded_calls == [{"text": "Hola", "repeats": 2, "provider": "cuda"}]


def test_profile_run_without_out_writes_to_the_default_wav_file(
    monkeypatch, tmp_path, capsys
):
    """Verifies --profile without --out saves into paths.DEFAULT_MELO_WAV_FILE."""
    default_path = tmp_path / "defaults" / "melo_es_0.wav"
    monkeypatch.setattr(paths, "DEFAULT_MELO_WAV_FILE", default_path)
    install_fake_profile(monkeypatch, {"wav_bytes": b"default-wav"})
    set_arguments(monkeypatch, "--profile")
    assert cli.main() == 0
    assert default_path.read_bytes() == b"default-wav"
    assert capsys.readouterr().out.splitlines()[-1] == f"WAV saved to {default_path}"


def test_plain_run_builds_the_harness_synthesizes_the_text_and_saves_the_wav(
    monkeypatch, tmp_path, build_wav
):
    """Verifies a plain run builds the harness with the provider, synthesizes the text and saves it."""
    wav = build_wav(frame_count=12346, sample_rate=10000, peak=12345)
    recorded_calls = install_fake_harness(monkeypatch, wav)
    out_path = tmp_path / "a" / "b" / "clip.wav"
    set_arguments(
        monkeypatch, "--text", "Hola", "--provider", "cuda", "--out", str(out_path)
    )
    assert cli.main() == 0
    assert recorded_calls == [("init", "cuda"), ("synthesize", "Hola")]
    assert out_path.read_bytes() == wav


def test_plain_run_prints_duration_rate_and_peak_with_two_decimals(
    monkeypatch, tmp_path, build_wav, capsys
):
    """Verifies the plain run prints duration and peak to two decimals with the sample rate."""
    wav = build_wav(frame_count=12346, sample_rate=10000, peak=12345)
    install_fake_harness(monkeypatch, wav)
    out_path = tmp_path / "clip.wav"
    set_arguments(monkeypatch, "--out", str(out_path))
    assert cli.main() == 0
    assert capsys.readouterr().out.splitlines() == [
        f"Synthesized 1.23s (10000 Hz, peak=0.38) -> {out_path}"
    ]


def test_plain_run_without_out_uses_the_default_text_and_wav_file(
    monkeypatch, tmp_path, build_wav
):
    """Verifies a plain run with no flags synthesizes the default sentence into the default file."""
    default_path = tmp_path / "defaults" / "melo_es_0.wav"
    monkeypatch.setattr(paths, "DEFAULT_MELO_WAV_FILE", default_path)
    wav = build_wav(frame_count=22050, sample_rate=22050)
    recorded_calls = install_fake_harness(monkeypatch, wav)
    set_arguments(monkeypatch)
    assert cli.main() == 0
    assert recorded_calls == [
        ("init", "cpu"),
        ("synthesize", DEFAULT_INTERVENTION_TEXT),
    ]
    assert default_path.read_bytes() == wav
