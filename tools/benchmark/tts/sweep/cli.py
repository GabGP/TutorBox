"""Command line of the TTS sweep: reads the flags, loads the corpus and writes the summary."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from tools.benchmark.tts.shared import paths
from tools.benchmark.tts.sweep.corpus import load_corpus_texts, select_evaluation_texts
from tools.benchmark.tts.sweep.engine_names import (
    DEFAULT_SWEEP_ENGINES,
    parse_engine_names,
)
from tools.benchmark.tts.sweep.report import write_summary
from tools.benchmark.tts.sweep.runner import run_sweep

DEFAULT_SWEEP_REPEATS: int = 3
EXIT_SUCCESS: int = 0
EXIT_EMPTY_CORPUS: int = 2


@dataclass(frozen=True)
class SweepOptions:
    """Validated options of one sweep run."""

    engines: list[str]
    repeats: int
    corpus_path: Path
    output_dir: Path
    language: str
    all_texts: bool


def parse_arguments() -> SweepOptions:
    """Parses the sweep flags; an unsupported engine list exits through the parser with code 2."""
    parser = argparse.ArgumentParser(description="TTS engine A/B sweep (Spanish-first)")
    parser.add_argument(
        "--engines",
        default=DEFAULT_SWEEP_ENGINES,
        help="comma list; canonical Qwen name is qwen3-tts (qwen is an alias)",
    )
    parser.add_argument("--repeats", type=int, default=DEFAULT_SWEEP_REPEATS)
    parser.add_argument("--corpus", default=str(paths.DEFAULT_CORPUS_FILE))
    parser.add_argument("--out", default=str(paths.DEFAULT_RESULTS_DIR))
    parser.add_argument("--lang", default="es")
    parser.add_argument(
        "--all-texts",
        action="store_true",
        help="evaluate all texts in corpus instead of only the first",
    )
    arguments = parser.parse_args()
    try:
        engines = parse_engine_names(arguments.engines)
    except ValueError as error:
        parser.error(str(error))
    return SweepOptions(
        engines=engines,
        repeats=arguments.repeats,
        corpus_path=Path(arguments.corpus),
        output_dir=Path(arguments.out),
        language=arguments.lang,
        all_texts=arguments.all_texts,
    )


def main() -> int:
    """Runs the engine x corpus sweep, writes its summary and returns the exit code."""
    options = parse_arguments()
    texts = load_corpus_texts(options.corpus_path)
    if not texts:
        print("empty corpus", file=sys.stderr)
        return EXIT_EMPTY_CORPUS

    wav_dir = options.output_dir / paths.WAV_SUBDIRECTORY_NAME
    wav_dir.mkdir(parents=True, exist_ok=True)
    rows = run_sweep(
        options.engines,
        select_evaluation_texts(texts, options.all_texts),
        language=options.language,
        repeats=options.repeats,
        wav_dir=wav_dir,
    )
    if rows:
        summary_file = write_summary(rows, options.output_dir)
        print(f"wrote {summary_file}")
    else:
        print("no rows generated", file=sys.stderr)
    return EXIT_SUCCESS
