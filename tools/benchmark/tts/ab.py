"""Sweep engines x corpus -> CSV + blind WAVs for jury listening.

Usage (repo root):
  python tools/benchmark/tts/ab.py --engines qwen3-tts,sherpa,piper,espeak --repeats 3
  python tools/benchmark/tts/ab.py --engines qwen3-tts,sherpa,piper --repeats 5 --out tools/benchmark/tts/results
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT_DIR = HERE.parent.parent.parent
BACKEND_SRC = ROOT_DIR / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.benchmark.tts.metrics import (
    _detect_engine_provider,
    profile_engine,
)

DEFAULT_SWEEP_REPEATS: int = 3
DEFAULT_SWEEP_ENGINES: str = "qwen3-tts,sherpa,piper,espeak"
MAX_ERROR_SNIPPET_CHARS: int = 160
MAX_TEXT_SNIPPET_CHARS: int = 80
FIRST_CORPUS_ENTRY_INDEX: int = 0
EXIT_SUCCESS: int = 0
EXIT_EMPTY_CORPUS: int = 2

SUPPORTED_ENGINES: frozenset[str] = frozenset(
    {"qwen3-tts", "sherpa", "piper", "espeak", "kokoro", "melo", "moss-nano"}
)
ENGINE_ALIASES: dict[str, str] = {"qwen": "qwen3-tts"}

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


def _get_fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    """Orders summary CSV columns logically, appending any unexpected fields at the end."""
    all_keys = {k for r in rows for k in r}
    ordered = [col for col in COLUMNS_ORDER if col in all_keys]
    extras = sorted(all_keys - set(ordered))
    return ordered + extras


def _normalize_engine_name(name: str) -> str:
    """Returns the canonical benchmark name while retaining the short Qwen alias."""
    normalized = name.strip().lower()
    return ENGINE_ALIASES.get(normalized, normalized)


def _parse_engine_names(raw: str) -> list[str]:
    """Normalizes, de-duplicates, and validates comma-separated engine names."""
    names = [_normalize_engine_name(name) for name in raw.split(",") if name.strip()]
    unsupported = [name for name in names if name not in SUPPORTED_ENGINES]
    if unsupported:
        listed = ", ".join(dict.fromkeys(unsupported))
        raise ValueError(f"unsupported engine(s): {listed}; use qwen3-tts for Qwen")
    if not names:
        raise ValueError("--engines must contain at least one engine")
    return list(dict.fromkeys(names))


def main() -> int:
    ap = argparse.ArgumentParser(description="TTS engine A/B sweep (Spanish-first)")
    ap.add_argument(
        "--engines",
        default=DEFAULT_SWEEP_ENGINES,
        help="comma list; canonical Qwen name is qwen3-tts (qwen is an alias)",
    )
    ap.add_argument("--repeats", type=int, default=DEFAULT_SWEEP_REPEATS)
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "es_math.txt"))
    ap.add_argument("--out", default=str(HERE / "results"))
    ap.add_argument("--lang", default="es")
    ap.add_argument(
        "--all-texts",
        action="store_true",
        help="evaluate all texts in corpus instead of only the first",
    )
    args = ap.parse_args()
    try:
        engines = _parse_engine_names(args.engines)
    except ValueError as err:
        ap.error(str(err))

    texts = [
        ln.strip()
        for ln in Path(args.corpus).read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    if not texts:
        print("empty corpus", file=sys.stderr)
        return EXIT_EMPTY_CORPUS

    out, wavdir = Path(args.out), Path(args.out) / "out"
    wavdir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    eval_texts = (
        list(enumerate(texts))
        if args.all_texts
        else [(FIRST_CORPUS_ENTRY_INDEX, texts[FIRST_CORPUS_ENTRY_INDEX])]
    )

    for eng in engines:
        for idx, text in eval_texts:
            try:
                stats = profile_engine(eng, text, lang=args.lang, repeats=args.repeats)
            except (
                RuntimeError,
                OSError,
                ValueError,
                ImportError,
            ) as err:  # missing model/dep
                print(f"[{eng}] unavailable: {err}")
                rows.append(
                    {
                        "engine": eng,
                        "provider": _detect_engine_provider(eng),
                        "text_idx": idx,
                        "error": str(err)[:MAX_ERROR_SNIPPET_CHARS],
                    }
                )
                continue

            name = wavdir / f"{eng}_{args.lang}_{idx}.wav"
            name.write_bytes(stats.wav_bytes)
            row = stats.summary() | {
                "wav": str(name),
                "text": text[:MAX_TEXT_SNIPPET_CHARS],
                "text_idx": idx,
            }
            rows.append(row)  # type: ignore[arg-type]
            print(
                f"[{eng}:{row.get('provider', 'cpu')} #{idx}] cold={row['cold_first_s']}s warm_p50={row['warm_p50_s']}s "
                f"rtf={row['rtf_p50']} peak={row['peak']} rss+{row['rss_delta_mb']}MB vram+{row.get('vram_delta_mb', 0.0)}MB "
                f"({row.get('rss_scope', 'unknown')}) -> {name}"
            )

    if rows:
        with open(out / "summary.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=_get_fieldnames(rows))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {out / 'summary.csv'}")
    else:
        print("no rows generated", file=sys.stderr)
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
