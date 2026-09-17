"""Unit tests for Qwen3-TTS command runner and timing parser."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from core.config import get_settings
from core.tts.engines.qwen import QwenBackend
from core.tts.engines.qwen.models import QwenModelPaths
from core.tts.engines.qwen.runner import build_qwen_command, parse_qwen_timings


def test_build_qwen_command_basic(tmp_path):
    paths = QwenModelPaths(
        model_path=tmp_path / "model.gguf",
        mmproj_path=tmp_path / "mmproj.gguf",
        bin_path=tmp_path / "llama-tts.exe",
    )
    out_wav = tmp_path / "out.wav"
    cfg = get_settings().tts
    cmd = build_qwen_command(paths, "Hola clase", "es", out_wav, cfg)

    assert str(paths.bin_path) in cmd
    assert "-m" in cmd
    assert str(paths.model_path) == cmd[cmd.index("-m") + 1]
    assert "-p" in cmd
    assert "Hola clase" == cmd[cmd.index("-p") + 1]
    assert "-o" in cmd
    assert str(out_wav) == cmd[cmd.index("-o") + 1]
    assert "--tts-speaker-file" not in cmd


def test_build_qwen_command_with_speaker(tmp_path):
    paths = QwenModelPaths(
        model_path=tmp_path / "model.gguf",
        mmproj_path=tmp_path / "mmproj.gguf",
        bin_path=tmp_path / "llama-tts.exe",
    )
    speaker = tmp_path / "ref.wav"
    speaker.write_bytes(b"wav")
    cfg = get_settings().tts
    cmd = build_qwen_command(
        paths, "Texto", "es", tmp_path / "out.wav", cfg, speaker_file=speaker
    )
    assert "--tts-speaker-file" in cmd
    assert str(speaker) == cmd[cmd.index("--tts-speaker-file") + 1]


def test_parse_qwen_timings_complete():
    stdout = (
        "0.04.145.928 I timings: prompt eval 0.05s + generation 2.05s + "
        "vocoder 0.06s = total 2.16s\n0.04.145.929 I output audio = 9.04s"
    )
    res = parse_qwen_timings(stdout)
    assert res["prompt_eval"] == 0.05
    assert res["generation"] == 2.05
    assert res["vocoder"] == 0.06
    assert res["total"] == 2.16
    assert res["synthesis_s"] == 2.16


def test_parse_qwen_timings_partial():
    stdout = "timings: prompt eval 0.04s + generation 0.3s"
    res = parse_qwen_timings(stdout)
    assert res["prompt_eval"] == 0.04
    assert res["generation"] == 0.3
    assert res["synthesis_s"] == 0.34


def test_parse_qwen_timings_empty():
    assert parse_qwen_timings("No timing info present") == {}


def test_qwen_backend_records_timings(monkeypatch, tmp_path):
    models_dir = tmp_path / "models" / "tts" / "qwen"
    models_dir.mkdir(parents=True, exist_ok=True)
    model = models_dir / "Qwen3-TTS-12Hz-1.7B-Base-Q4_K_M.gguf"
    model.write_bytes(b"dummy")
    mmproj = models_dir / "mmproj-Qwen3-TTS-12Hz-1.7B-Base-Q8_0.gguf"
    mmproj.write_bytes(b"dummy")
    bin_dir = tmp_path / "bin" / "llama"
    bin_dir.mkdir(parents=True, exist_ok=True)
    binary = bin_dir / "llama-tts.exe"
    binary.write_bytes(b"dummy")

    monkeypatch.setenv("TTS_QWEN_GGUF_PATH", str(model))

    backend = QwenBackend()
    assert backend.last_synthesis_seconds is None
    assert backend.last_timings == {}

    def fake_subprocess_run(cmd, **_kwargs):
        out_idx = cmd.index("-o") + 1
        Path(cmd[out_idx]).write_bytes(b"RIFF....WAVEfmt ....data....")
        res = MagicMock(returncode=0)
        res.stdout = "timings: prompt eval 0.05s + generation 2.05s + vocoder 0.06s = total 2.16s"
        return res

    with patch("subprocess.run", side_effect=fake_subprocess_run):
        backend.synthesize("Hola clase")

    assert backend.last_synthesis_seconds == 2.16
    assert backend.last_timings["generation"] == 2.05

    backend.unload()
    assert backend.last_synthesis_seconds is None
    assert backend.last_timings == {}
