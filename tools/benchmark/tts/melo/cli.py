"""Command line entry point for the MeloTTS Spanish ONNX harness: synthesize or profile."""

from __future__ import annotations

import argparse
from pathlib import Path

from tools.benchmark.tts.audio.wav_analysis import analyze_wav
from tools.benchmark.tts.melo.harness import MeloTTSHarness
from tools.benchmark.tts.melo.profiler import DEFAULT_WARM_REPEATS, profile_melo
from tools.benchmark.tts.shared import paths
from tools.benchmark.tts.shared.sample_text import DEFAULT_INTERVENTION_TEXT


def parse_arguments() -> argparse.Namespace:
    """Reads the harness flags from the command line."""
    parser = argparse.ArgumentParser(description="MeloTTS Spanish ONNX harness")
    parser.add_argument(
        "--text",
        default=DEFAULT_INTERVENTION_TEXT,
        help="Text to synthesize",
    )
    parser.add_argument("--out", default=None, help="Output WAV path")
    parser.add_argument(
        "--repeats", type=int, default=DEFAULT_WARM_REPEATS, help="Warm repetitions"
    )
    parser.add_argument("--provider", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--profile", action="store_true", help="Run full latency sweep")
    return parser.parse_args()


def _resolve_output_path(out: str | None) -> Path:
    """Returns the requested WAV path, or the default melo WAV file when none is given."""
    return Path(out or paths.DEFAULT_MELO_WAV_FILE)


def _write_wav(out_path: Path, wav_bytes: bytes) -> None:
    """Writes WAV bytes to out_path, creating any missing parent folders first."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(wav_bytes)


def _run_profile(arguments: argparse.Namespace) -> None:
    """Profiles the text, prints every figure except the audio, and saves the WAV."""
    print(f"Profiling MeloTTS Spanish [{arguments.provider}]...")
    stats = profile_melo(
        arguments.text, repeats=arguments.repeats, provider=arguments.provider
    )
    for stat_name, stat_value in stats.items():
        if stat_name != "wav_bytes":
            print(f"  {stat_name}: {stat_value}")

    out_path = _resolve_output_path(arguments.out)
    _write_wav(out_path, stats["wav_bytes"])
    print(f"WAV saved to {out_path}")


def _run_synthesis(arguments: argparse.Namespace) -> None:
    """Synthesizes the text once, saves the WAV and prints its duration, rate and peak."""
    harness = MeloTTSHarness(provider=arguments.provider)
    wav_bytes = harness.synthesize(arguments.text)
    out_path = _resolve_output_path(arguments.out)
    _write_wav(out_path, wav_bytes)
    duration, sample_rate, peak = analyze_wav(wav_bytes)
    print(
        f"Synthesized {duration:.2f}s ({sample_rate} Hz, peak={peak:.2f}) -> {out_path}"
    )


def main() -> int:
    """Runs the latency sweep when --profile is given, otherwise a single synthesis."""
    arguments = parse_arguments()
    if arguments.profile:
        _run_profile(arguments)
    else:
        _run_synthesis(arguments)
    return 0
