"""Engine x text sweep: profiles each pair, writes its WAV and collects its summary row."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.benchmark.tts.profiling import backend_bridge
from tools.benchmark.tts.profiling.engine_run import profile_engine
from tools.benchmark.tts.profiling.results import EngineStats

MAX_ERROR_SNIPPET_CHARS: int = 160
MAX_TEXT_SNIPPET_CHARS: int = 80
PROFILING_ERRORS: tuple[type[Exception], ...] = (
    RuntimeError,
    OSError,
    ValueError,
    ImportError,
)


def run_sweep(
    engines: list[str],
    evaluation_texts: list[tuple[int, str]],
    *,
    language: str,
    repeats: int,
    wav_dir: Path,
) -> list[dict[str, Any]]:
    """Profiles every engine on every selected text, engines outer and texts inner."""
    rows: list[dict[str, Any]] = []
    for engine in engines:
        for text_index, text in evaluation_texts:
            row = _profile_pair(
                engine,
                text_index,
                text,
                language=language,
                repeats=repeats,
                wav_dir=wav_dir,
            )
            rows.append(row)
    return rows


def _profile_pair(
    engine: str,
    text_index: int,
    text: str,
    *,
    language: str,
    repeats: int,
    wav_dir: Path,
) -> dict[str, Any]:
    """Profiles one engine on one text and returns the row describing the outcome."""
    try:
        stats = profile_engine(engine, text, lang=language, repeats=repeats)
    except PROFILING_ERRORS as error:
        return _unavailable_row(engine, text_index, error)
    return _profiled_row(
        engine, text_index, text, stats, language=language, wav_dir=wav_dir
    )


def _unavailable_row(engine: str, text_index: int, error: Exception) -> dict[str, Any]:
    """Prints the unavailable line for a missing engine or model and builds its error row."""
    print(f"[{engine}] unavailable: {error}")
    return {
        "engine": engine,
        "provider": backend_bridge.detect_engine_provider(engine),
        "text_idx": text_index,
        "error": str(error)[:MAX_ERROR_SNIPPET_CHARS],
    }


def _profiled_row(
    engine: str,
    text_index: int,
    text: str,
    stats: EngineStats,
    *,
    language: str,
    wav_dir: Path,
) -> dict[str, Any]:
    """Writes the synthesized WAV, builds the summary row and prints its progress line."""
    wav_path = wav_dir / f"{engine}_{language}_{text_index}.wav"
    wav_path.write_bytes(stats.wav_bytes)
    row = stats.summary() | {
        "wav": str(wav_path),
        "text": text[:MAX_TEXT_SNIPPET_CHARS],
        "text_idx": text_index,
    }
    print(_format_progress_line(engine, text_index, row, wav_path))
    return row


def _format_progress_line(
    engine: str, text_index: int, row: dict[str, Any], wav_path: Path
) -> str:
    """Formats the one-line progress report of one profiled engine and text."""
    engine_label = f"[{engine}:{row.get('provider', 'cpu')} #{text_index}]"
    timing_figures = (
        f"cold={row['cold_first_s']}s warm_p50={row['warm_p50_s']}s "
        f"rtf={row['rtf_p50']} peak={row['peak']}"
    )
    memory_figures = (
        f"rss+{row['rss_delta_mb']}MB vram+{row.get('vram_delta_mb', 0.0)}MB "
        f"({row.get('rss_scope', 'unknown')})"
    )
    return f"{engine_label} {timing_figures} {memory_figures} -> {wav_path}"
