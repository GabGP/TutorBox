"""Command building and timing extraction for Qwen3-TTS llama-tts executor."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from core.config.models import TTSConfig
from core.tts.constants import SUBPROCESS_SUCCESS_EXIT_CODE
from core.tts.engines.qwen.models import QwenModelPaths
from core.tts.exceptions import TTSSynthesisError

__all__ = [
    "build_qwen_command",
    "build_qwen_daemon_command",
    "execute_qwen_cli",
    "parse_qwen_timings",
]


def build_qwen_command(
    paths: QwenModelPaths,
    text: str,
    lang: str,
    out_wav: Path,
    tts_cfg: TTSConfig,
    speaker_file: Path | None = None,
) -> list[str]:
    """Assembles the CLI argument list for invoking one-shot llama-tts."""
    cmd = [
        str(paths.bin_path),
        "-m",
        str(paths.model_path),
        "-mm",
        str(paths.mmproj_path),
        "-c",
        str(tts_cfg.qwen_context),
        "-ngl",
        "99",
        "-t",
        str(tts_cfg.qwen_threads),
        "-s",
        str(tts_cfg.qwen_seed),
        "--tts-lang",
        lang,
        "-p",
        text,
        "-o",
        str(out_wav),
    ]
    if speaker_file:
        cmd.extend(("--tts-speaker-file", str(speaker_file)))
    return cmd


def build_qwen_daemon_command(
    paths: QwenModelPaths,
    tts_cfg: TTSConfig,
    speaker_file: Path | None = None,
) -> list[str]:
    """Assembles the CLI argument list for spawning persistent llama-tts-daemon."""
    bin_to_use = paths.daemon_bin_path or paths.bin_path
    cmd = [
        str(bin_to_use),
        "-m",
        str(paths.model_path),
        "-mm",
        str(paths.mmproj_path),
        "-c",
        str(tts_cfg.qwen_context),
        "-ngl",
        "99",
        "-t",
        str(tts_cfg.qwen_threads),
        "-s",
        str(tts_cfg.qwen_seed),
        "--daemon",
    ]
    if speaker_file:
        cmd.extend(("--tts-speaker-file", str(speaker_file)))
    return cmd


def execute_qwen_cli(
    paths: QwenModelPaths,
    text: str,
    lang: str,
    wav: Path,
    cfg: TTSConfig,
    speaker_file: Path | None = None,
) -> str:
    """Executes one-shot CLI llama-tts and returns stdout."""
    cmd = build_qwen_command(paths, text, lang, wav, cfg, speaker_file=speaker_file)
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=cfg.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as err:
        raise TTSSynthesisError(
            f"Qwen synthesis timed out after {cfg.timeout_seconds}s."
        ) from err
    if proc.returncode != SUBPROCESS_SUCCESS_EXIT_CODE or not wav.exists():
        raise TTSSynthesisError(f"Qwen synthesis failed: {proc.stdout}")
    return proc.stdout


def parse_qwen_timings(output: str) -> dict[str, float]:
    """Extracts neural inference and vocoder timings from daemon or CLI output."""
    timings: dict[str, float] = {}
    if "DONE\t" in output or "total=" in output:
        for match in re.finditer(r"([a-zA-Z_]+)=([\d\.]+)", output):
            key, val = match.group(1), float(match.group(2))
            timings[key] = val
        if "total" in timings:
            timings["synthesis_s"] = timings["total"]
        elif timings:
            timings["synthesis_s"] = round(sum(timings.values()), 4)
        return timings

    for pattern, key in (
        (r"prompt eval\s+([\d\.]+)s", "prompt_eval"),
        (r"generation\s+([\d\.]+)s", "generation"),
        (r"vocoder\s+([\d\.]+)s", "vocoder"),
        (r"total\s+([\d\.]+)s", "total"),
    ):
        m = re.search(pattern, output)
        if m:
            timings[key] = float(m.group(1))

    if "total" in timings:
        timings["synthesis_s"] = timings["total"]
    elif timings:
        timings["synthesis_s"] = round(sum(timings.values()), 4)

    return timings
