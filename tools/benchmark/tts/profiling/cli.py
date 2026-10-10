"""Command-line entry point that profiles one speech synthesis and prints its metrics."""

from __future__ import annotations

import argparse
import os

from tools.benchmark.tts.profiling.single_run import profile_speech_synthesis
from tools.benchmark.tts.shared.sample_text import DEFAULT_INTERVENTION_TEXT
from tools.benchmark.tts.shared.units import BYTES_PER_KB


def parse_arguments() -> argparse.Namespace:
    """Parses the benchmark command line into engine, text, language and voice."""
    parser = argparse.ArgumentParser(
        description="Benchmark Utz'tutor offline speech synthesis"
    )
    parser.add_argument(
        "--engine",
        default=os.environ.get("TTS_ENGINE", "piper"),
        help="TTS engine to profile (default: piper or $TTS_ENGINE)",
    )
    parser.add_argument(
        "--text",
        default=DEFAULT_INTERVENTION_TEXT,
        help="Text to synthesize",
    )
    parser.add_argument("--lang", default="es", help="Language code (default: es)")
    parser.add_argument("--voice", default=None, help="Voice identifier (optional)")
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint for running diagnostic benchmark on the appliance."""
    arguments = parse_arguments()

    print(f"Benchmarking Utz'tutor Neural TTS Pipeline [{arguments.engine}]...")
    result = profile_speech_synthesis(
        arguments.text,
        lang=arguments.lang,
        voice=arguments.voice,
        engine=arguments.engine,
    )
    print(f"Latency:      {result.latency_seconds:.3f} s")
    print(f"Audio Length: {result.audio_duration_seconds:.2f} s")
    print(f"RTF:          {result.real_time_factor:.3f}x")
    print(f"Sample Rate:  {result.sample_rate} Hz")
    print(f"Peak Level:   {result.peak_amplitude:.2f} (normalized)")
    print(f"WAV Size:     {result.audio_byte_count / BYTES_PER_KB:.1f} KB")
