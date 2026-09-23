"""Standalone inference and profiling harness for MeloTTS Spanish ONNX model.

Part of TutorBox Phase 3 (Spike Candidate 4).
Usage:
    python tools/benchmark/tts/harness_melo.py --text "Hola mundo" --out tools/benchmark/tts/results/out/melo_test.wav
    python tools/benchmark/tts/harness_melo.py --profile
"""

from __future__ import annotations

import argparse
import gc
import io
import re
import sys
import time
import wave
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
BACKEND_SRC = REPO_ROOT / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.benchmark.tts.metrics import (
    BYTES_PER_KB,
    _analyze_wav,
    _rss_mb,
)

DEFAULT_MODEL_DIR = REPO_ROOT / ".cache" / "models" / "tts" / "melo"
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_SPEED = 1.0

# Phonetic overrides for common pedagogical/mathematical Spanish terms and digits
PHONETIC_OVERRIDES: dict[str, list[str]] = {
    "100": ["s", "j", "e", "n"],
    "por": ["p", "o", "r"],
    "ciento": ["s", "j", "e", "n", "t", "o"],
    "del": ["d", "e", "l"],
    "grupo": ["g", "r", "u", "p", "o"],
    "respondió": ["r", "e", "s", "p", "o", "n", "d", "j", "o"],
    "un": ["u", "n"],
    "medio": ["m", "e", "d", "j", "o"],
    "dividiste": ["d", "i", "b", "i", "d", "i", "s", "t", "e"],
    "sólo": ["s", "o", "l", "o"],
    "el": ["e", "l"],
    "numerador": ["n", "u", "m", "e", "r", "a", "d", "o", "r"],
    "denominador": ["d", "e", "n", "o", "m", "i", "n", "a", "d", "o", "r"],
    "denominadores": ["d", "e", "n", "o", "m", "i", "n", "a", "d", "o", "r", "e", "s"],
    "entre": ["e", "n", "t", "r", "e"],
    "2": ["d", "o", "s"],
    "5": ["s", "i", "n", "k", "o"],
    "60": ["s", "e", "s", "e", "n", "t", "a"],
    "80": ["o", "ch", "e", "n", "t", "a"],
    "la": ["l", "a"],
    "respuesta": ["r", "e", "s", "p", "w", "e", "s", "t", "a"],
    "correcta": ["k", "o", "r", "e", "k", "t", "a"],
    "es": ["e", "s"],
    "tres": ["t", "r", "e", "s"],
    "cuartos": ["k", "w", "a", "r", "t", "o", "s"],
    "sextos": ["s", "e", "k", "s", "t", "o", "s"],
    "tercios": ["t", "e", "r", "s", "j", "o", "s"],
    "resta": ["r", "e", "s", "t", "a"],
    "sumaste": ["s", "u", "m", "a", "s", "t", "e"],
    "confundiste": ["k", "o", "n", "f", "u", "n", "d", "i", "s", "t", "e"],
    "atención": ["a", "t", "e", "n", "s", "j", "o", "n"],
}


class MeloTTSHarness:
    """Standalone inference harness for MeloTTS Spanish ONNX model."""

    def __init__(
        self,
        model_dir: Path | str = DEFAULT_MODEL_DIR,
        provider: str = "cpu",
    ) -> None:
        self.model_dir = Path(model_dir)
        self.provider = provider
        self.model_path = self.model_dir / "model.onnx"
        self.lexicon_path = self.model_dir / "lexicon.txt"
        self.tokens_path = self.model_dir / "tokens.txt"

        self._session: ort.InferenceSession | None = None
        self._lexicon: dict[str, list[str]] = {}
        self._token2id: dict[str, int] = {}
        self._load_support_files()

    def _load_support_files(self) -> None:
        """Loads Spanish lexicon dictionary and token mappings."""
        if self.tokens_path.exists():
            for line in self.tokens_path.read_text(encoding="utf-8").splitlines():
                parts = line.strip().split()
                if len(parts) == 2:
                    self._token2id[parts[0]] = int(parts[1])

        if self.lexicon_path.exists():
            for line in self.lexicon_path.read_text(encoding="utf-8").splitlines():
                parts = line.strip().split()
                if len(parts) >= 3 and len(parts[1:]) % 2 == 0:
                    n = len(parts[1:]) // 2
                    self._lexicon[parts[0].lower()] = parts[1 : 1 + n]

    def load(self) -> float:
        """Loads the ONNX runtime session and returns duration in ms."""
        t0 = time.perf_counter()
        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if self.provider == "cuda"
            else ["CPUExecutionProvider"]
        )
        self._session = ort.InferenceSession(str(self.model_path), providers=providers)
        return (time.perf_counter() - t0) * 1000.0

    def unload(self) -> None:
        """Unloads the ONNX runtime session."""
        self._session = None
        gc.collect()

    def is_loaded(self) -> bool:
        """Returns True if the session is currently active in memory."""
        return self._session is not None

    def text_to_token_ids(self, text: str) -> list[int]:
        """Converts Spanish text into interspersed phoneme token sequence."""
        words = re.findall(
            r"[\w\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]+|[.,:;!?]", text.lower()
        )
        seq: list[int] = []
        sp_id = self._token2id.get("SP", 0)

        for w in words:
            if w in self._token2id:
                seq.append(self._token2id[w])
            elif w in PHONETIC_OVERRIDES:
                for ph in PHONETIC_OVERRIDES[w]:
                    if ph in self._token2id:
                        seq.append(self._token2id[ph])
            elif w in self._lexicon:
                for ph in self._lexicon[w]:
                    if ph in self._token2id:
                        seq.append(self._token2id[ph])
            else:
                for ch in w:
                    if ch in self._token2id:
                        seq.append(self._token2id[ch])
            seq.append(sp_id)

        # Intersperse with 0 (blank symbol)
        interspersed = [0] * (len(seq) * 2 + 1)
        interspersed[1::2] = seq
        return interspersed

    def synthesize(
        self,
        text: str,
        speed: float = DEFAULT_SPEED,
    ) -> bytes:
        """Synthesizes text into 16-bit mono 44.1 kHz WAV bytes."""
        if self._session is None:
            self.load()
        assert self._session is not None

        token_ids = self.text_to_token_ids(text)
        x = np.array([token_ids], dtype=np.int64)
        x_lengths = np.array([x.shape[1]], dtype=np.int64)
        tones = np.zeros_like(x, dtype=np.int64)
        sid = np.array([0], dtype=np.int64)
        noise_scale = np.array([0.667], dtype=np.float32)
        length_scale = np.array([1.0 / max(0.1, speed)], dtype=np.float32)
        noise_scale_w = np.array([0.8], dtype=np.float32)

        inputs = {
            "x": x,
            "x_lengths": x_lengths,
            "tones": tones,
            "sid": sid,
            "noise_scale": noise_scale,
            "length_scale": length_scale,
            "noise_scale_w": noise_scale_w,
        }

        outputs = self._session.run(None, inputs)
        audio = outputs[0].squeeze()

        # Convert float32 [-1, 1] to 16-bit PCM WAV
        int16_audio = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(DEFAULT_SAMPLE_RATE)
            wf.writeframes(int16_audio.tobytes())
        return buffer.getvalue()


def profile_melo(
    text: str,
    repeats: int = 5,
    provider: str = "cpu",
) -> dict[str, Any]:
    """Profiles MeloTTS cold load, warm latency, RTF, and acoustic properties."""
    harness = MeloTTSHarness(provider=provider)
    harness.unload()

    rss_before = _rss_mb()
    load_ms = harness.load()

    # Cold synthesis
    t0_synth = time.perf_counter()
    wav_bytes = harness.synthesize(text)
    cold_synth_s = time.perf_counter() - t0_synth
    rss_after = _rss_mb()

    cold_first_s = (load_ms / 1000.0) + cold_synth_s
    rss_delta_mb = max(0.0, rss_after - rss_before)

    # Warm runs
    warm_latencies: list[float] = []
    for _ in range(max(1, repeats)):
        t_start = time.perf_counter()
        wav_bytes = harness.synthesize(text)
        warm_latencies.append(time.perf_counter() - t_start)

    duration, sample_rate, peak = _analyze_wav(wav_bytes)
    warm_p50 = float(np.median(warm_latencies))
    warm_p95 = float(np.percentile(warm_latencies, 95))
    rtf_p50 = warm_p50 / duration if duration > 0 else 0.0

    return {
        "engine": "melo",
        "provider": provider,
        "cold_first_s": round(cold_first_s, 3),
        "warm_p50_s": round(warm_p50, 3),
        "warm_p95_s": round(warm_p95, 3),
        "rtf_p50": round(rtf_p50, 4),
        "peak": round(peak, 3),
        "load_ms": round(load_ms, 2),
        "rss_delta_mb": round(rss_delta_mb, 2),
        "sr_hz": sample_rate,
        "wav_kb": round(len(wav_bytes) / BYTES_PER_KB, 1),
        "duration_s": round(duration, 3),
        "wav_bytes": wav_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MeloTTS Spanish ONNX harness")
    parser.add_argument(
        "--text",
        default=(
            "Atención: 100 por ciento del grupo respondió un medio. "
            "Dividiste sólo el numerador entre 2. La respuesta correcta es tres cuartos."
        ),
        help="Text to synthesize",
    )
    parser.add_argument("--out", default=None, help="Output WAV path")
    parser.add_argument("--repeats", type=int, default=5, help="Warm repetitions")
    parser.add_argument("--provider", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--profile", action="store_true", help="Run full latency sweep")
    args = parser.parse_args()

    if args.profile:
        print(f"Profiling MeloTTS Spanish [{args.provider}]...")
        stats = profile_melo(args.text, repeats=args.repeats, provider=args.provider)
        for k, v in stats.items():
            if k != "wav_bytes":
                print(f"  {k}: {v}")

        out_path = Path(args.out or HERE / "results" / "out" / "melo_es_0.wav")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(stats["wav_bytes"])
        print(f"WAV saved to {out_path}")
    else:
        harness = MeloTTSHarness(provider=args.provider)
        wav = harness.synthesize(args.text)
        out_path = Path(args.out or HERE / "results" / "out" / "melo_es_0.wav")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(wav)
        dur, sr, peak = _analyze_wav(wav)
        print(f"Synthesized {dur:.2f}s ({sr} Hz, peak={peak:.2f}) -> {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
