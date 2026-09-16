"""Sweep engines x corpus -> CSV + blind WAVs for jury listening.

Usage (repo root):
  uv run python benchmark/tts/ab.py --engines piper --repeats 3
  uv run python benchmark/tts/ab.py --engines piper,sherpa,moss-nano --repeats 5 --out benchmark/tts/results
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

from benchmark.tts.metrics import _detect_engine_provider, profile_engine

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


def main() -> int:
    ap = argparse.ArgumentParser(description="TTS engine A/B sweep (Spanish-first)")
    ap.add_argument("--engines", default="piper", help="comma list, e.g. piper,espeak")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--corpus", default=str(HERE / "corpus" / "es_math.txt"))
    ap.add_argument("--out", default=str(HERE / "results"))
    ap.add_argument("--lang", default="es")
    ap.add_argument(
        "--all-texts",
        action="store_true",
        help="evaluate all texts in corpus instead of only the first",
    )
    args = ap.parse_args()

    texts = [
        ln.strip()
        for ln in Path(args.corpus).read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    if not texts:
        print("empty corpus", file=sys.stderr)
        return 2

    out, wavdir = Path(args.out), Path(args.out) / "out"
    wavdir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    eval_texts = list(enumerate(texts)) if args.all_texts else [(0, texts[0])]

    for eng in [e.strip() for e in args.engines.split(",") if e.strip()]:
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
                        "error": str(err)[:160],
                    }
                )
                continue

            name = wavdir / f"{eng}_es_{idx}.wav"
            name.write_bytes(stats.wav_bytes)
            row = stats.summary() | {
                "wav": str(name),
                "text": text[:80],
                "text_idx": idx,
            }
            rows.append(row)  # type: ignore[arg-type]
            print(
                f"[{eng}:{row.get('provider', 'cpu')} #{idx}] cold={row['cold_first_s']}s warm_p50={row['warm_p50_s']}s "
                f"rtf={row['rtf_p50']} peak={row['peak']} rss+{row['rss_delta_mb']}MB -> {name}"
            )

    if rows:
        with open(out / "summary.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=_get_fieldnames(rows))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {out / 'summary.csv'}")
    else:
        print("no rows generated", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
