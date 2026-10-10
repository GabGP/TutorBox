"""Timing decisions for the cold and warm turns of one engine profile."""

from __future__ import annotations

from tools.benchmark.tts.shared.units import MILLISECONDS_PER_SECOND


def split_cold_timing(
    preload_load_ms: float,
    synthesis_latency_seconds: float,
    backend_synthesis_seconds: float | None,
) -> tuple[float, float]:
    """Splits the cold turn into its model load in milliseconds and its first-run seconds."""
    # In a preloaded quiz turn scenario, the cold turn absorbs both model load and first synthesis.
    if preload_load_ms > 0:
        load_ms = preload_load_ms
        cold_first_seconds = (
            load_ms / MILLISECONDS_PER_SECOND
        ) + synthesis_latency_seconds
    elif backend_synthesis_seconds is not None and backend_synthesis_seconds > 0:
        load_ms = max(
            0.0,
            (synthesis_latency_seconds - backend_synthesis_seconds)
            * MILLISECONDS_PER_SECOND,
        )
        cold_first_seconds = synthesis_latency_seconds
    else:
        load_ms = preload_load_ms
        cold_first_seconds = (
            load_ms / MILLISECONDS_PER_SECOND
        ) + synthesis_latency_seconds
    return load_ms, cold_first_seconds


def effective_warm_latency(
    backend_synthesis_seconds: object, wall_latency_seconds: float
) -> float:
    """Prefers the backend's own synthesis time when it reports a positive number."""
    # Unlike the cold check, this one rejects non-numbers before comparing them.
    if (
        isinstance(backend_synthesis_seconds, (int, float))
        and backend_synthesis_seconds > 0
    ):
        return backend_synthesis_seconds
    return wall_latency_seconds
