"""Summary CSV column ordering and writing for the TTS sweep."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

SUMMARY_FILE_NAME: str = "summary.csv"

COLUMNS_ORDER: tuple[str, ...] = (
    "engine",
    "provider",
    "cold_first_s",
    "warm_p50_s",
    "warm_p95_s",
    "rtf_p50",
    "peak",
    "load_ms",
    "rss_delta_mb",
    "vram_delta_mb",
    "rss_scope",
    "sr_hz",
    "wav_kb",
    "wav",
    "text_idx",
    "text",
    "error",
)


def get_fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    """Orders known summary columns first, then any unexpected keys sorted."""
    all_keys = {key for row in rows for key in row}
    ordered = [column_name for column_name in COLUMNS_ORDER if column_name in all_keys]
    extras = sorted(all_keys - set(ordered))
    return ordered + extras


def write_summary(rows: list[dict[str, Any]], output_dir: Path) -> Path:
    """Writes the summary CSV into output_dir; the directory must already exist."""
    summary_file = output_dir / SUMMARY_FILE_NAME
    with open(summary_file, "w", newline="", encoding="utf-8") as summary_handle:
        writer = csv.DictWriter(summary_handle, fieldnames=get_fieldnames(rows))
        writer.writeheader()
        writer.writerows(rows)
    return summary_file
