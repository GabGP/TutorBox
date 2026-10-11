"""Cold and warm synthesis runs of one engine, summarized as EngineStats."""

from __future__ import annotations

from tools.benchmark.tts.memory import MemoryMonitor
from tools.benchmark.tts.profiling import backend_bridge
from tools.benchmark.tts.profiling.load_timing import (
    effective_warm_latency,
    split_cold_timing,
)
from tools.benchmark.tts.profiling.results import EngineStats, ProfileResult
from tools.benchmark.tts.profiling.synthesis import make_profile_result, synthesize_once

DEFAULT_PROFILE_REPEATS: int = 5


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
    router = backend_bridge.get_tts_router()
    router.unload(engine)

    with MemoryMonitor() as tracker:
        _, preload_load_ms = router.preload(engine=engine, lang=lang, voice=voice)
        wav_bytes, synthesis_latency_seconds = synthesize_once(
            text, lang=lang, voice=voice, engine=engine, router=router
        )

    backend = router.get_backend(engine)
    backend_synthesis_seconds = getattr(backend, "last_synthesis_seconds", None)
    load_ms, cold_first_seconds = split_cold_timing(
        preload_load_ms, synthesis_latency_seconds, backend_synthesis_seconds
    )
    cold_result = make_profile_result(
        text,
        wav_bytes,
        cold_first_seconds,
        load_ms=load_ms,
        rss_delta_mb=tracker.rss_delta_mb,
        vram_delta_mb=tracker.vram_delta_mb,
        rss_scope=tracker.scope,
        cold=True,
    )

    runs = [cold_result]
    last_wav_bytes = wav_bytes
    for _ in range(max(0, repeats - 1)):
        last_wav_bytes, warm_result = _profile_warm_turn(
            text, lang, voice, engine, backend, tracker
        )
        runs.append(warm_result)

    active_provider = backend_bridge.detect_engine_provider(engine)
    return EngineStats(
        engine=engine,
        runs=tuple(runs),
        wav_bytes=last_wav_bytes,
        provider=active_provider,
    )


def _profile_warm_turn(
    text: str,
    lang: str,
    voice: str | None,
    engine: str,
    backend: object | None,
    tracker: MemoryMonitor,
) -> tuple[bytes, ProfileResult]:
    """Runs one warm synthesis, preferring the backend's own time when it reports one."""
    backend_bridge.get_tts_router()  # warm path reuses active router and voice
    wav_bytes, wall_latency_seconds = synthesize_once(
        text, lang=lang, voice=voice, engine=engine
    )
    backend_synthesis_seconds = getattr(backend, "last_synthesis_seconds", None)
    warm_latency_seconds = effective_warm_latency(
        backend_synthesis_seconds, wall_latency_seconds
    )
    warm_result = make_profile_result(
        text,
        wav_bytes,
        warm_latency_seconds,
        rss_delta_mb=tracker.rss_delta_mb,
        vram_delta_mb=tracker.vram_delta_mb,
        rss_scope=tracker.scope,
        cold=False,
    )
    return wav_bytes, warm_result
