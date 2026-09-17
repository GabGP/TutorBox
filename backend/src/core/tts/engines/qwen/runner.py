"""Command building and timing extraction for Qwen3-TTS llama-tts executor."""

from __future__ import annotations

import re
from pathlib import Path

from core.config.models import TTSConfig
from core.tts.engines.qwen.models import QwenModelPaths

__all__ = ["build_qwen_command", "parse_qwen_timings"]


def build_qwen_command(
    paths: QwenModelPaths,
    text: str,
    lang: str,
    out_wav: Path,
    tts_cfg: TTSConfig,
    speaker_file: Path | None = None,
) -> list[str]:
    """Assembles the CLI argument list for invoking llama-tts."""
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


def parse_qwen_timings(output: str) -> dict[str, float]:
    """Extracts internal neural inference and vocoder timings from llama-tts stdout."""
    timings: dict[str, float] = {}
    p_m = re.search(r"prompt eval\s+([\d\.]+)s", output)
    if p_m:
        timings["prompt_eval"] = float(p_m.group(1))

    g_m = re.search(r"generation\s+([\d\.]+)s", output)
    if g_m:
        timings["generation"] = float(g_m.group(1))

    v_m = re.search(r"vocoder\s+([\d\.]+)s", output)
    if v_m:
        timings["vocoder"] = float(v_m.group(1))

    t_m = re.search(r"total\s+([\d\.]+)s", output)
    if t_m:
        val = float(t_m.group(1))
        timings["total"] = val
        timings["synthesis_s"] = val
    elif timings:
        timings["synthesis_s"] = round(sum(timings.values()), 4)

    return timings
