"""TTS latency, acoustic, and A/B metrics module.

Migrated from backend/src/core/tts/profiler.py to serve as the unified home
for speech synthesis benchmarking: single-run profiling, CLI diagnostic runs,
and multi-engine comparative A/B sweeps (cold vs warm, RTF, peak amplitude,
load duration, and memory footprint).

Usage:
    # Single-run diagnostic CLI:
    python tools/benchmark/tts/metrics.py --engine piper

    # Programmatic single-run profiler:
    from tools.benchmark.tts.metrics import profile_speech_synthesis
    res = profile_speech_synthesis("Hola mundo", lang="es")

    # Multi-engine comparative sweep:
    from tools.benchmark.tts.metrics import profile_engine
    stats = profile_engine("piper", "Hola mundo", repeats=3)
"""

from __future__ import annotations

import argparse
import importlib
import io
import os
import statistics
import struct
import sys
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_SRC = ROOT_DIR / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.benchmark.tts.memory import (
    MemoryMonitor,
    get_host_rss_mb,
    is_jetson_uma,
)

__all__ = [
    "BYTES_PER_KB",
    "BYTES_PER_MB",
    "COLD_RUN_INDEX",
    "DECIMAL_PLACES_DURATION",
    "DECIMAL_PLACES_LATENCY",
    "DECIMAL_PLACES_METRIC",
    "DECIMAL_PLACES_PEAK",
    "DECIMAL_PLACES_RTF",
    "DECIMAL_PLACES_WAV_KB",
    "DEFAULT_PROFILE_REPEATS",
    "EngineStats",
    "KILOBYTES_PER_MB",
    "MILLISECONDS_PER_SECOND",
    "PCM_16BIT_MAX_FLOAT",
    "PCM_SAMPLE_WIDTH_BYTES",
    "PERCENTILE_95",
    "ProfileResult",
    "RSS_MEASUREMENT_SCOPE",
    "WARM_RUN_START_INDEX",
    "main",
    "profile_engine",
    "profile_speech_synthesis",
]

PERCENTILE_95: float = 0.95
DEFAULT_PROFILE_REPEATS: int = 5
COLD_RUN_INDEX: int = 0
WARM_RUN_START_INDEX: int = 1

DECIMAL_PLACES_LATENCY: int = 3
DECIMAL_PLACES_RTF: int = 4
DECIMAL_PLACES_PEAK: int = 3
DECIMAL_PLACES_METRIC: int = 2
DECIMAL_PLACES_DURATION: int = 3
DECIMAL_PLACES_WAV_KB: int = 1

BYTES_PER_KB: float = 1024.0
BYTES_PER_MB: float = 1024.0 * 1024.0
KILOBYTES_PER_MB: float = 1024.0
MILLISECONDS_PER_SECOND: float = 1000.0
PCM_SAMPLE_WIDTH_BYTES: int = 2  # 16-bit linear PCM (2 bytes per sample)
PCM_16BIT_MAX_FLOAT: float = 32768.0
RSS_MEASUREMENT_SCOPE: str = "parent-process-only"


@dataclass(frozen=True)
class ProfileResult:
    """Benchmark metrics for a single speech synthesis run."""

    text: str
    latency_seconds: float
    audio_duration_seconds: float
    real_time_factor: float
    sample_rate: int
    peak_amplitude: float
    audio_byte_count: int
    load_ms: float = 0.0
    rss_delta_mb: float = 0.0
    vram_delta_mb: float = 0.0
    cold: bool = False
    rss_scope: str = RSS_MEASUREMENT_SCOPE


@dataclass(frozen=True)
class EngineStats:
    """Aggregated multi-run benchmark metrics for an engine."""

    engine: str
    runs: tuple[ProfileResult, ...]
    wav_bytes: bytes  # last warm run audio bytes for evaluation
    provider: str = "cpu"

    @property
    def warm(self) -> tuple[ProfileResult, ...]:
        """Returns only the warm synthesis runs (excluding cold first run)."""
        return self.runs[WARM_RUN_START_INDEX:] if len(self.runs) > 1 else self.runs

    def summary(self) -> dict[str, float | str | int]:
        """Calculates percentile latencies, RTF, peak level, and cold load footprint."""
        latencies = sorted(run.latency_seconds for run in self.warm)
        real_time_factors = sorted(run.real_time_factor for run in self.warm)
        first_run = self.runs[COLD_RUN_INDEX]
        last_run = self.runs[-1]
        p95_index = max(
            0, min(len(latencies) - 1, int(len(latencies) * PERCENTILE_95))
        )

        return {
            "engine": self.engine,
            "provider": self.provider,
            "cold_first_s": round(
                first_run.latency_seconds, DECIMAL_PLACES_LATENCY
            ),
            "warm_p50_s": round(
                statistics.median(latencies), DECIMAL_PLACES_LATENCY
            ),
            "warm_p95_s": round(latencies[p95_index], DECIMAL_PLACES_LATENCY),
            "rtf_p50": round(
                statistics.median(real_time_factors), DECIMAL_PLACES_RTF
            ),
            "peak": round(last_run.peak_amplitude, DECIMAL_PLACES_PEAK),
            "sr_hz": last_run.sample_rate,
            "wav_kb": round(
                last_run.audio_byte_count / BYTES_PER_KB,
                DECIMAL_PLACES_WAV_KB,
            ),
            "load_ms": round(first_run.load_ms, DECIMAL_PLACES_METRIC),
            "rss_delta_mb": round(
                first_run.rss_delta_mb, DECIMAL_PLACES_METRIC
            ),
            "vram_delta_mb": round(
                first_run.vram_delta_mb, DECIMAL_PLACES_METRIC
            ),
            "rss_scope": first_run.rss_scope,
        }


def _analyze_wav(wav_bytes: bytes) -> tuple[float, int, float]:
    """Extracts audio duration (s), sample rate (Hz), and normalized peak amplitude."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        num_channels = wav_file.getnchannels()
        raw_frames = wav_file.readframes(wav_file.getnframes())

    frame_size = sample_width * num_channels
    actual_frames = len(raw_frames) // frame_size if frame_size > 0 else 0
    duration = actual_frames / float(sample_rate) if sample_rate > 0 else 0.0

    if actual_frames == 0 or sample_width != PCM_SAMPLE_WIDTH_BYTES:
        return duration, sample_rate, 0.0

    sample_count = len(raw_frames) // PCM_SAMPLE_WIDTH_BYTES
    samples = struct.unpack(
        f"<{sample_count}h", raw_frames[: sample_count * PCM_SAMPLE_WIDTH_BYTES]
    )
    peak = (
        max((abs(sample) for sample in samples), default=0.0)
        / PCM_16BIT_MAX_FLOAT
    )
    return duration, sample_rate, peak


def _rss_mb() -> float:
    """Returns current process resident set size in megabytes across platforms."""
    return get_host_rss_mb()


def _get_tts_router() -> Any:
    """Lazily loads and returns the active backend TTSRouter singleton."""
    router_module = importlib.import_module("core.tts.router")
    return router_module.get_tts_router()


def _synthesize_once(
    text: str,
    lang: str = "es",
    voice: str | None = None,
    engine: str | None = None,
    router: Any | None = None,
) -> tuple[bytes, float]:
    """Synthesizes text once bypassing the LRU cache and returns (wav_bytes, elapsed_seconds)."""
    active_router = router or _get_tts_router()
    active_router.clear_cache()

    start_time = time.perf_counter()
    wav_bytes = active_router.synthesize(text, lang=lang, voice=voice, backend=engine)
    latency_seconds = time.perf_counter() - start_time
    return wav_bytes, latency_seconds


def _make_profile_result(
    text: str,
    wav_bytes: bytes,
    latency_seconds: float,
    *,
    load_ms: float = 0.0,
    rss_delta_mb: float = 0.0,
    vram_delta_mb: float = 0.0,
    rss_scope: str = RSS_MEASUREMENT_SCOPE,
    cold: bool = False,
) -> ProfileResult:
    """Constructs a ProfileResult from synthesis artifacts and timing."""
    duration, sample_rate, peak = _analyze_wav(wav_bytes)
    real_time_factor = latency_seconds / duration if duration > 0 else 0.0

    return ProfileResult(
        text=text,
        latency_seconds=round(latency_seconds, DECIMAL_PLACES_RTF),
        audio_duration_seconds=round(duration, DECIMAL_PLACES_DURATION),
        real_time_factor=(
            round(real_time_factor, DECIMAL_PLACES_RTF) if duration > 0 else 0.0
        ),
        sample_rate=sample_rate,
        peak_amplitude=round(peak, DECIMAL_PLACES_PEAK),
        audio_byte_count=len(wav_bytes),
        load_ms=round(load_ms, DECIMAL_PLACES_METRIC),
        rss_delta_mb=round(rss_delta_mb, DECIMAL_PLACES_METRIC),
        vram_delta_mb=round(vram_delta_mb, DECIMAL_PLACES_METRIC),
        cold=cold,
        rss_scope=rss_scope,
    )


def profile_speech_synthesis(
    text: str,
    lang: str = "es",
    voice: str | None = None,
    *,
    engine: str | None = None,
) -> ProfileResult:
    """Measures synthesis wall-clock latency, RTF, and acoustic properties."""
    with MemoryMonitor() as tracker:
        wav_bytes, latency = _synthesize_once(text, lang=lang, voice=voice, engine=engine)
    return _make_profile_result(
        text,
        wav_bytes,
        latency,
        rss_delta_mb=tracker.rss_delta_mb,
        vram_delta_mb=tracker.vram_delta_mb,
        rss_scope=tracker.scope,
    )


def profile_engine(
    engine: str,
    text: str,
    lang: str = "es",
    voice: str | None = None,
    repeats: int = DEFAULT_PROFILE_REPEATS,
) -> EngineStats:
    """Measures cold-start initialization and warm repeated runs for an engine.

    NO FALLBACK: If the engine backend or model weights are missing, raises
    TTSUnavailableError immediately so callers can distinguish failures.
    """
    router = _get_tts_router()
    router.unload(engine)

    with MemoryMonitor() as tracker:
        _, preload_load_ms = router.preload(engine=engine, lang=lang, voice=voice)
        wav_bytes, synth_latency = _synthesize_once(
            text, lang=lang, voice=voice, engine=engine, router=router
        )

    backend = router.get_backend(engine)
    last_synth_s = getattr(backend, "last_synthesis_seconds", None)

    # In a preloaded quiz turn scenario, the cold turn absorbs both model load and first synthesis.
    if preload_load_ms > 0:
        load_ms = preload_load_ms
        cold_first_s = (load_ms / MILLISECONDS_PER_SECOND) + synth_latency
    elif last_synth_s is not None and last_synth_s > 0:
        load_ms = max(0.0, (synth_latency - last_synth_s) * MILLISECONDS_PER_SECOND)
        cold_first_s = synth_latency
    else:
        load_ms = preload_load_ms
        cold_first_s = (load_ms / MILLISECONDS_PER_SECOND) + synth_latency

    rss_delta = tracker.rss_delta_mb
    vram_delta = tracker.vram_delta_mb
    scope = tracker.scope

    runs = [
        _make_profile_result(
            text,
            wav_bytes,
            cold_first_s,
            load_ms=load_ms,
            rss_delta_mb=rss_delta,
            vram_delta_mb=vram_delta,
            rss_scope=scope,
            cold=True,
        )
    ]

    for _ in range(max(0, repeats - 1)):
        _get_tts_router()  # warm path reuses active router and voice
        wav_bytes, warm_wall_latency = _synthesize_once(
            text, lang=lang, voice=voice, engine=engine
        )
        warm_synth = getattr(backend, "last_synthesis_seconds", None)
        effective_warm = (
            warm_synth
            if isinstance(warm_synth, (int, float)) and warm_synth > 0
            else warm_wall_latency
        )
        runs.append(
            _make_profile_result(
                text,
                wav_bytes,
                effective_warm,
                rss_delta_mb=rss_delta,
                vram_delta_mb=vram_delta,
                rss_scope=scope,
                cold=False,
            )
        )

    active_provider = _detect_engine_provider(engine)
    return EngineStats(
        engine=engine,
        runs=tuple(runs),
        wav_bytes=wav_bytes,
        provider=active_provider,
    )


def _detect_engine_provider(engine: str) -> str:
    """Returns the resolved execution provider ('cpu' or 'cuda') for an engine."""
    if engine in ("qwen3-tts", "qwen"):
        try:
            qwen_models = importlib.import_module("core.tts.engines.qwen.models")
            return qwen_models.detect_qwen_provider()
        except Exception:
            return "cpu"
    if engine in ("kokoro", "sherpa"):
        try:
            config_module = importlib.import_module("core.config")
            provider_module = importlib.import_module("core.tts.engines.provider")

            tts_cfg = config_module.get_settings().tts
            cfg_val = (
                tts_cfg.kokoro_provider
                if engine == "kokoro"
                else tts_cfg.sherpa_provider
            )
            return provider_module.resolve_execution_provider(cfg_val)
        except Exception:
            return "cpu"
    return "cpu"


def main() -> None:
    """CLI entrypoint for running diagnostic benchmark on the appliance."""
    parser = argparse.ArgumentParser(
        description="Benchmark TutorBox offline speech synthesis"
    )
    parser.add_argument(
        "--engine",
        default=os.environ.get("TTS_ENGINE", "piper"),
        help="TTS engine to profile (default: piper or $TTS_ENGINE)",
    )
    parser.add_argument(
        "--text",
        default=(
            "Atención: 100 por ciento del grupo respondió un medio. "
            "Dividiste sólo el numerador entre 2. La respuesta correcta es tres cuartos."
        ),
        help="Text to synthesize",
    )
    parser.add_argument("--lang", default="es", help="Language code (default: es)")
    parser.add_argument("--voice", default=None, help="Voice identifier (optional)")
    args = parser.parse_args()

    print(f"Benchmarking TutorBox Neural TTS Pipeline [{args.engine}]...")
    res = profile_speech_synthesis(
        args.text, lang=args.lang, voice=args.voice, engine=args.engine
    )
    print(f"Latency:      {res.latency_seconds:.3f} s")
    print(f"Audio Length: {res.audio_duration_seconds:.2f} s")
    print(f"RTF:          {res.real_time_factor:.3f}x")
    print(f"Sample Rate:  {res.sample_rate} Hz")
    print(f"Peak Level:   {res.peak_amplitude:.2f} (normalized)")
    print(f"WAV Size:     {res.audio_byte_count / BYTES_PER_KB:.1f} KB")


if __name__ == "__main__":
    main()
