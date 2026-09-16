"""TTS latency, acoustic, and A/B metrics module.

Migrated from backend/src/core/tts/profiler.py to serve as the unified home
for speech synthesis benchmarking: single-run profiling, CLI diagnostic runs,
and multi-engine comparative A/B sweeps (cold vs warm, RTF, peak amplitude,
load duration, and memory footprint).

Usage:
    # Single-run diagnostic CLI:
    python benchmark/tts/metrics.py --engine piper

    # Programmatic single-run profiler:
    from benchmark.tts.metrics import profile_speech_synthesis
    res = profile_speech_synthesis("Hola mundo", lang="es")

    # Multi-engine comparative sweep:
    from benchmark.tts.metrics import profile_engine
    stats = profile_engine("piper", "Hola mundo", repeats=3)
"""

from __future__ import annotations

import argparse
import io
import os
import statistics
import struct
import sys
import time
import wave
from dataclasses import dataclass
from pathlib import Path

from core.tts.router import TTSRouter, get_tts_router

__all__ = [
    "EngineStats",
    "ProfileResult",
    "main",
    "profile_engine",
    "profile_speech_synthesis",
]


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
    cold: bool = False


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
        return self.runs[1:] if len(self.runs) > 1 else self.runs

    def summary(self) -> dict[str, float | str | int]:
        """Calculates percentile latencies, RTF, peak level, and cold load footprint."""
        latencies = sorted(run.latency_seconds for run in self.warm)
        real_time_factors = sorted(run.real_time_factor for run in self.warm)
        first_run = self.runs[0]
        last_run = self.runs[-1]
        p95_index = max(0, min(len(latencies) - 1, int(len(latencies) * 0.95)))

        return {
            "engine": self.engine,
            "provider": self.provider,
            "cold_first_s": round(first_run.latency_seconds, 3),
            "warm_p50_s": round(statistics.median(latencies), 3),
            "warm_p95_s": round(latencies[p95_index], 3),
            "rtf_p50": round(statistics.median(real_time_factors), 4),
            "peak": round(last_run.peak_amplitude, 3),
            "sr_hz": last_run.sample_rate,
            "wav_kb": round(last_run.audio_byte_count / 1024, 1),
            "load_ms": round(first_run.load_ms, 2),
            "rss_delta_mb": round(first_run.rss_delta_mb, 2),
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

    if actual_frames == 0 or sample_width != 2:
        return duration, sample_rate, 0.0

    sample_count = len(raw_frames) // 2
    samples = struct.unpack(f"<{sample_count}h", raw_frames[: sample_count * 2])
    peak = max(abs(sample) for sample in samples) / 32768.0
    return duration, sample_rate, peak


def _rss_mb() -> float:
    """Returns current process resident set size in megabytes across platforms."""
    # 1. Preferred cross-platform if psutil is installed
    try:
        import psutil  # pyright: ignore[reportMissingImports,reportMissingModuleSource]

        return float(psutil.Process().memory_info().rss) / (1024.0 * 1024.0)
    except (ImportError, AttributeError):
        pass

    # 2. Windows native memory query via GetProcessMemoryInfo
    try:
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]

        get_mem_info = ctypes.windll.psapi.GetProcessMemoryInfo
        get_mem_info.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
            wintypes.DWORD,
        ]
        get_mem_info.restype = wintypes.BOOL
        counters = PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
        if get_mem_info(
            ctypes.windll.kernel32.GetCurrentProcess(),
            ctypes.byref(counters),
            counters.cb,
        ):
            return float(counters.WorkingSetSize) / (1024.0 * 1024.0)
    except Exception:
        pass

    # 3. Linux /proc/self/status query
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except OSError:
        pass

    # 4. Unix resource fallback
    if sys.platform != "win32":
        try:
            import resource  # pyright: ignore[reportMissingImports]

            getrusage = getattr(resource, "getrusage", None)
            rusage_self = getattr(resource, "RUSAGE_SELF", None)
            if callable(getrusage) and rusage_self is not None:
                return float(getrusage(rusage_self).ru_maxrss) / 1024.0
        except (ImportError, AttributeError):
            pass

    return 0.0


def _synthesize_once(
    text: str,
    lang: str = "es",
    voice: str | None = None,
    engine: str | None = None,
    router: TTSRouter | None = None,
) -> tuple[bytes, float]:
    """Synthesizes text once bypassing the LRU cache and returns (wav_bytes, elapsed_seconds)."""
    active_router = router or get_tts_router()
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
    cold: bool = False,
) -> ProfileResult:
    """Constructs a ProfileResult from synthesis artifacts and timing."""
    duration, sample_rate, peak = _analyze_wav(wav_bytes)
    real_time_factor = latency_seconds / duration if duration > 0 else 0.0

    return ProfileResult(
        text=text,
        latency_seconds=round(latency_seconds, 4),
        audio_duration_seconds=round(duration, 3),
        real_time_factor=round(real_time_factor, 4) if duration > 0 else 0.0,
        sample_rate=sample_rate,
        peak_amplitude=round(peak, 3),
        audio_byte_count=len(wav_bytes),
        load_ms=round(load_ms, 2),
        rss_delta_mb=round(rss_delta_mb, 2),
        cold=cold,
    )


def profile_speech_synthesis(
    text: str,
    lang: str = "es",
    voice: str | None = None,
    *,
    engine: str | None = None,
) -> ProfileResult:
    """Measures synthesis wall-clock latency, RTF, and acoustic properties."""
    wav_bytes, latency = _synthesize_once(text, lang=lang, voice=voice, engine=engine)
    return _make_profile_result(text, wav_bytes, latency)


def profile_engine(
    engine: str,
    text: str,
    lang: str = "es",
    voice: str | None = None,
    repeats: int = 5,
) -> EngineStats:
    """Measures cold-start initialization and warm repeated runs for an engine.

    NO FALLBACK: If the engine backend or model weights are missing, raises
    TTSUnavailableError immediately so callers can distinguish failures.
    """
    router = get_tts_router()
    router.unload(engine)

    rss_before = _rss_mb()
    # Explicit preload measures model loading duration in milliseconds separately from synthesis
    # Does not swallow exceptions: if the engine is missing, it will fail fast here.
    _, load_ms = router.preload(engine=engine, lang=lang, voice=voice)

    wav_bytes, synth_latency = _synthesize_once(
        text, lang=lang, voice=voice, engine=engine, router=router
    )
    rss_after = _rss_mb()
    cold_first_s = (load_ms / 1000.0) + synth_latency
    rss_delta = max(0.0, rss_after - rss_before)

    runs = [
        _make_profile_result(
            text,
            wav_bytes,
            cold_first_s,
            load_ms=load_ms,
            rss_delta_mb=rss_delta,
            cold=True,
        )
    ]

    for _ in range(max(0, repeats - 1)):
        get_tts_router()  # warm path reuses active router and voice
        wav_bytes, warm_latency = _synthesize_once(
            text, lang=lang, voice=voice, engine=engine
        )
        runs.append(_make_profile_result(text, wav_bytes, warm_latency, cold=False))

    active_provider = _detect_engine_provider(engine)
    return EngineStats(
        engine=engine,
        runs=tuple(runs),
        wav_bytes=wav_bytes,
        provider=active_provider,
    )


def _detect_engine_provider(engine: str) -> str:
    """Returns the resolved execution provider ('cpu' or 'cuda') for an engine."""
    if engine in ("kokoro", "sherpa"):
        try:
            from core.config import get_settings
            from core.tts.engines.provider import resolve_execution_provider

            tts_cfg = get_settings().tts
            cfg_val = (
                tts_cfg.kokoro_provider
                if engine == "kokoro"
                else tts_cfg.sherpa_provider
            )
            return resolve_execution_provider(cfg_val)
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
    print(f"WAV Size:     {res.audio_byte_count / 1024:.1f} KB")


if __name__ == "__main__":
    main()
