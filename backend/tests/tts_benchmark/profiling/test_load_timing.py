"""Verifies the cold-turn timing split and the warm latency choice of an engine profile."""

import pytest

from tools.benchmark.tts.profiling.load_timing import (
    effective_warm_latency,
    split_cold_timing,
)


def test_preloaded_turn_adds_the_preload_load_to_the_first_synthesis():
    """Verifies a positive preload load is reported and added to the first synthesis."""
    load_ms, cold_first_seconds = split_cold_timing(120.5, 0.25, None)
    assert load_ms == 120.5
    assert cold_first_seconds == pytest.approx(0.3705)


def test_preloaded_turn_ignores_the_backend_synthesis_time():
    """Verifies a positive preload load wins even when the backend reports a figure."""
    load_ms, cold_first_seconds = split_cold_timing(120.5, 0.25, 9.0)
    assert load_ms == 120.5
    assert cold_first_seconds == pytest.approx(0.3705)


def test_backend_figure_splits_load_out_of_the_wall_latency():
    """Verifies the load is the wall latency minus the backend synthesis, in milliseconds."""
    load_ms, cold_first_seconds = split_cold_timing(0.0, 0.5, 0.2)
    assert load_ms == pytest.approx(300.0)
    assert cold_first_seconds == 0.5


def test_backend_figure_above_the_wall_latency_gives_zero_load():
    """Verifies the load never goes negative when the backend reports more than the wall time."""
    load_ms, cold_first_seconds = split_cold_timing(0.0, 0.2, 0.5)
    assert load_ms == 0.0
    assert cold_first_seconds == 0.2


def test_missing_backend_figure_keeps_the_preload_value():
    """Verifies a missing backend figure falls back to the preload value and wall latency."""
    load_ms, cold_first_seconds = split_cold_timing(0.0, 0.4, None)
    assert load_ms == 0.0
    assert cold_first_seconds == 0.4


def test_zero_backend_figure_keeps_the_preload_value():
    """Verifies a zero backend figure falls back to the preload value and wall latency."""
    load_ms, cold_first_seconds = split_cold_timing(0.0, 0.4, 0.0)
    assert load_ms == 0.0
    assert cold_first_seconds == 0.4


def test_non_positive_preload_value_passes_through_unchanged():
    """Verifies a negative preload value is kept as it is when no backend figure exists."""
    load_ms, cold_first_seconds = split_cold_timing(-5.0, 0.4, None)
    assert load_ms == -5.0
    assert cold_first_seconds == pytest.approx(0.395)


def test_effective_warm_latency_returns_the_backend_float():
    """Verifies a positive backend float replaces the wall latency."""
    assert effective_warm_latency(0.25, 0.9) == 0.25


def test_effective_warm_latency_returns_the_backend_int():
    """Verifies a positive backend int replaces the wall latency and keeps its type."""
    result = effective_warm_latency(2, 0.9)
    assert result == 2
    assert isinstance(result, int)


@pytest.mark.parametrize(
    "backend_value",
    [None, 0, -0.5, "0.3", object()],
    ids=["none", "zero", "negative", "string", "object"],
)
def test_effective_warm_latency_falls_back_to_wall_time(backend_value):
    """Verifies a missing, non-positive or non-numeric backend figure keeps the wall latency."""
    assert effective_warm_latency(backend_value, 0.9) == 0.9
