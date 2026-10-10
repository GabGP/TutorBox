"""Single-run profiler: one timed synthesis with the host memory it touches."""

from __future__ import annotations

from tools.benchmark.tts.memory import MemoryMonitor
from tools.benchmark.tts.profiling.results import ProfileResult
from tools.benchmark.tts.profiling.synthesis import make_profile_result, synthesize_once


def profile_speech_synthesis(
    text: str,
    lang: str = "es",
    voice: str | None = None,
    *,
    engine: str | None = None,
) -> ProfileResult:
    """Measures synthesis wall-clock latency, RTF, and acoustic properties."""
    with MemoryMonitor() as tracker:
        wav_bytes, synthesis_latency_seconds = synthesize_once(
            text, lang=lang, voice=voice, engine=engine
        )
    return make_profile_result(
        text,
        wav_bytes,
        synthesis_latency_seconds,
        rss_delta_mb=tracker.rss_delta_mb,
        vram_delta_mb=tracker.vram_delta_mb,
        rss_scope=tracker.scope,
    )
