"""Verifies the timed single synthesis and the profile record built from its audio."""

import time

import pytest

from tools.benchmark.tts.profiling import backend_bridge
from tools.benchmark.tts.profiling.synthesis import make_profile_result, synthesize_once

SAMPLE_TEXT = "hola"
SYNTHESIZE_CALL = ("synthesize", SAMPLE_TEXT, "es", None, None)


@pytest.fixture
def clock_readings(monkeypatch):
    """Replaces time.perf_counter with a clock that advances a quarter second per reading."""
    readings: list[float] = []

    def fake_perf_counter() -> float:
        """Returns the next clock reading and records it."""
        reading = len(readings) * 0.25
        readings.append(reading)
        return reading

    monkeypatch.setattr(time, "perf_counter", fake_perf_counter)
    return readings


def test_cache_is_cleared_before_the_synthesis_call(fake_router):
    """Verifies the cache is cleared right before the router is asked to synthesize."""
    synthesize_once(SAMPLE_TEXT, router=fake_router)
    assert fake_router.calls == [("clear_cache",), SYNTHESIZE_CALL]


def test_text_language_voice_and_engine_reach_the_router(fake_router):
    """Verifies text, lang and voice are passed on and the engine is sent as the backend."""
    synthesize_once(
        SAMPLE_TEXT, lang="en", voice="amy", engine="piper", router=fake_router
    )
    assert fake_router.calls == [
        ("clear_cache",),
        ("synthesize", SAMPLE_TEXT, "en", "amy", "piper"),
    ]


def test_latency_is_the_difference_of_two_clock_readings(fake_router, clock_readings):
    """Verifies the audio is returned with the latency taken from exactly two clock readings."""
    wav_bytes, latency_seconds = synthesize_once(SAMPLE_TEXT, router=fake_router)
    assert wav_bytes == fake_router.wav_bytes
    assert latency_seconds == 0.25
    assert clock_readings == [0.0, 0.25]


def test_explicit_router_is_used_without_the_bridge_lookup(monkeypatch, fake_router):
    """Verifies a router passed in is synthesized with and the bridge is never consulted."""

    def refuse_bridge_lookup():
        """Fails the test when the bridge router is requested."""
        raise AssertionError("the bridge router must not be looked up")

    monkeypatch.setattr(backend_bridge, "get_tts_router", refuse_bridge_lookup)
    synthesize_once(SAMPLE_TEXT, router=fake_router)
    assert fake_router.calls == [("clear_cache",), SYNTHESIZE_CALL]


def test_bridge_router_is_used_when_no_router_is_given(fake_router):
    """Verifies synthesize_once falls back to the router the backend bridge returns."""
    wav_bytes, _ = synthesize_once(SAMPLE_TEXT)
    assert wav_bytes == fake_router.wav_bytes
    assert fake_router.calls == [("clear_cache",), SYNTHESIZE_CALL]


def test_latency_is_rounded_to_four_decimals(build_wav):
    """Verifies the latency keeps four decimal places."""
    result = make_profile_result(SAMPLE_TEXT, build_wav(), 0.123456)
    assert result.latency_seconds == 0.1235


def test_duration_and_sample_rate_come_from_the_wav(build_wav):
    """Verifies the duration keeps three decimals and the sample rate is read from the WAV."""
    result = make_profile_result(SAMPLE_TEXT, build_wav(frame_count=10000), 0.1)
    assert result.audio_duration_seconds == 0.454
    assert result.sample_rate == 22050


def test_peak_is_normalized_and_rounded_to_three_decimals(build_wav):
    """Verifies the peak is scaled by 16-bit full scale and rounded to three decimals."""
    wav_bytes = build_wav(frame_count=10000, peak=12345)
    result = make_profile_result(SAMPLE_TEXT, wav_bytes, 0.1)
    assert result.peak_amplitude == 0.377


def test_real_time_factor_is_latency_over_duration_rounded_to_four_decimals(
    build_wav,
):
    """Verifies the real-time factor is latency divided by duration, to four decimals."""
    wav_bytes = build_wav(frame_count=10000)
    result = make_profile_result(SAMPLE_TEXT, wav_bytes, 0.123456)
    assert result.real_time_factor == 0.2722


def test_zero_frame_clip_has_zero_duration_peak_and_real_time_factor(build_wav):
    """Verifies an empty clip reports zero duration, zero peak and a zero real-time factor."""
    result = make_profile_result(SAMPLE_TEXT, build_wav(frame_count=0), 0.25)
    assert result.audio_duration_seconds == 0.0
    assert result.real_time_factor == 0.0
    assert result.peak_amplitude == 0.0
    assert result.latency_seconds == 0.25


def test_audio_byte_count_is_the_length_of_the_wav_bytes(build_wav):
    """Verifies the byte count is the full length of the WAV container."""
    wav_bytes = build_wav()
    result = make_profile_result(SAMPLE_TEXT, wav_bytes, 0.1)
    assert result.audio_byte_count == len(wav_bytes)


def test_load_and_memory_are_rounded_to_two_decimals_and_stored(build_wav):
    """Verifies load time and memory deltas keep two decimals and are stored as given."""
    result = make_profile_result(
        SAMPLE_TEXT,
        build_wav(),
        0.1,
        load_ms=123.456,
        rss_delta_mb=3.14159,
        vram_delta_mb=2.71828,
    )
    assert result.load_ms == 123.46
    assert result.rss_delta_mb == 3.14
    assert result.vram_delta_mb == 2.72


def test_defaults_describe_a_warm_run_with_parent_process_scope(build_wav):
    """Verifies the optional arguments default to a warm run measured in the parent process."""
    result = make_profile_result(SAMPLE_TEXT, build_wav(), 0.1)
    assert result.text == SAMPLE_TEXT
    assert result.load_ms == 0.0
    assert result.rss_delta_mb == 0.0
    assert result.vram_delta_mb == 0.0
    assert result.cold is False
    assert result.rss_scope == "parent-process-only"


def test_cold_flag_and_rss_scope_are_stored_as_given(build_wav):
    """Verifies a cold flag and a custom RSS scope are kept on the result."""
    result = make_profile_result(
        SAMPLE_TEXT, build_wav(), 0.1, cold=True, rss_scope="uma-unified"
    )
    assert result.cold is True
    assert result.rss_scope == "uma-unified"
