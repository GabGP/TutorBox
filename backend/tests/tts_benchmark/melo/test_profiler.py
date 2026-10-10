"""Verifies profile_melo: harness lifecycle, cold and warm timing, rounding, RSS delta and report fields."""

import time

import pytest

from tools.benchmark.tts.melo import profiler
from tools.benchmark.tts.melo.profiler import (
    DEFAULT_WARM_REPEATS,
    WARM_PERCENTILE,
    profile_melo,
)

REPORT_KEYS = [
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
    "duration_s",
    "wav_bytes",
]
TEXT = "hola"
CLOCK_START_SECONDS = 100.0
DEFAULT_LOAD_MILLISECONDS = 250.0


class HarnessScript:
    """Scripts a fake MeloTTSHarness: records each call in order and returns WAV outputs in order."""

    def __init__(self, wav_outputs: list[bytes], load_milliseconds: float) -> None:
        self.calls: list[tuple] = []
        self.wav_outputs = wav_outputs
        self.load_milliseconds = load_milliseconds
        self.synthesize_count = 0

    def fake_harness_class(self) -> type:
        """Returns a MeloTTSHarness stand-in that reports every call to this script."""
        script = self

        class FakeMeloTTSHarness:
            """Stands in for MeloTTSHarness without loading any model."""

            def __init__(self, provider: str = "cpu") -> None:
                script.calls.append(("init", provider))

            def unload(self) -> None:
                script.calls.append(("unload",))

            def load(self) -> float:
                script.calls.append(("load",))
                return script.load_milliseconds

            def synthesize(self, text: str) -> bytes:
                script.calls.append(("synthesize", text))
                audio = script.wav_outputs[script.synthesize_count]
                script.synthesize_count += 1
                return audio

        return FakeMeloTTSHarness


def clock_readings(durations: list[float]) -> list[float]:
    """Builds perf_counter readings whose consecutive start and end pairs differ by the durations."""
    readings: list[float] = []
    now = CLOCK_START_SECONDS
    for duration in durations:
        readings.append(now)
        now += duration
        readings.append(now)
    return readings


def arrange(
    monkeypatch,
    wav_outputs: list[bytes],
    clock_durations: list[float],
    load_milliseconds: float = DEFAULT_LOAD_MILLISECONDS,
    rss_readings_mb: tuple[float, float] = (100.0, 100.0),
) -> HarnessScript:
    """Installs the fake harness, a scripted clock and scripted RSS readings for one run."""
    script = HarnessScript(wav_outputs, load_milliseconds)
    monkeypatch.setattr(profiler, "MeloTTSHarness", script.fake_harness_class())
    rss_iterator = iter(rss_readings_mb)
    monkeypatch.setattr(profiler, "get_host_rss_mb", lambda: next(rss_iterator))
    clock_iterator = iter(clock_readings(clock_durations))
    monkeypatch.setattr(time, "perf_counter", lambda: next(clock_iterator))
    return script


def test_default_warm_repeats_and_percentile_are_five_and_ninety_five():
    """Verifies the default warm repeat count is 5 and the warm percentile is 95."""
    assert DEFAULT_WARM_REPEATS == 5
    assert WARM_PERCENTILE == 95


def test_harness_gets_the_provider_then_is_unloaded_before_it_loads(
    monkeypatch, build_wav
):
    """Verifies the harness is built for the provider, unloaded, loaded, then synthesizes."""
    wav = build_wav(frame_count=22050, sample_rate=22050)
    script = arrange(monkeypatch, [wav] * 6, [0.5] + [0.25] * 5)
    profile_melo(TEXT, provider="cuda")
    assert script.calls == (
        [("init", "cuda"), ("unload",), ("load",)] + [("synthesize", TEXT)] * 6
    )


def test_provider_defaults_to_cpu_in_the_harness_and_the_report(monkeypatch, build_wav):
    """Verifies the cpu provider is used and reported when no provider is given."""
    wav = build_wav(frame_count=22050, sample_rate=22050)
    script = arrange(monkeypatch, [wav] * 2, [0.5, 0.25])
    report = profile_melo(TEXT, repeats=1)
    assert script.calls[0] == ("init", "cpu")
    assert report["provider"] == "cpu"


def test_cold_first_is_load_seconds_plus_the_timed_cold_synthesis(
    monkeypatch, build_wav
):
    """Verifies cold_first_s adds the load time in seconds to the cold synthesis time."""
    wav = build_wav(frame_count=22050, sample_rate=22050)
    arrange(monkeypatch, [wav, wav], [0.5, 0.25])
    report = profile_melo(TEXT, repeats=1)
    assert report["load_ms"] == 250.0
    assert report["cold_first_s"] == 0.75


def test_default_repeats_give_five_warm_syntheses_after_the_cold_one(
    monkeypatch, build_wav
):
    """Verifies the default run makes one cold and five warm synthesis calls."""
    wav = build_wav(frame_count=22050, sample_rate=22050)
    script = arrange(monkeypatch, [wav] * 6, [0.5] + [0.25] * 5)
    profile_melo(TEXT)
    assert script.synthesize_count == 6


@pytest.mark.parametrize("repeats", [0, -3])
def test_repeats_below_one_still_run_one_warm_synthesis(
    monkeypatch, build_wav, repeats
):
    """Verifies zero or negative repeats still give exactly one warm synthesis."""
    wav = build_wav(frame_count=22050, sample_rate=22050)
    script = arrange(monkeypatch, [wav, wav], [0.5, 0.25])
    profile_melo(TEXT, repeats=repeats)
    assert script.synthesize_count == 2


def test_warm_p50_and_p95_are_taken_over_the_warm_runs_only(monkeypatch, build_wav):
    """Verifies warm_p50_s is the median and warm_p95_s the 95th percentile of the warm runs."""
    wav = build_wav(frame_count=44100, sample_rate=22050)
    arrange(monkeypatch, [wav] * 6, [0.5, 0.25, 0.75, 1.0, 0.5, 2.0])
    report = profile_melo(TEXT)
    assert report["warm_p50_s"] == 0.75
    assert report["warm_p95_s"] == 1.8


def test_rtf_is_the_warm_median_divided_by_the_audio_duration(monkeypatch, build_wav):
    """Verifies rtf_p50 is the warm median latency over the duration of the last audio."""
    wav = build_wav(frame_count=44100, sample_rate=22050)
    arrange(monkeypatch, [wav] * 6, [0.5, 0.25, 0.75, 1.0, 0.5, 2.0])
    report = profile_melo(TEXT)
    assert report["duration_s"] == 2.0
    assert report["rtf_p50"] == 0.375


def test_rtf_is_zero_when_the_audio_has_no_duration(monkeypatch, build_wav):
    """Verifies rtf_p50 and duration_s are 0.0 for audio without frames."""
    silent_wav = build_wav(frame_count=0)
    arrange(monkeypatch, [silent_wav] * 2, [0.5, 0.25])
    report = profile_melo(TEXT, repeats=1)
    assert report["duration_s"] == 0.0
    assert report["rtf_p50"] == 0.0


def test_rss_delta_is_the_growth_between_the_two_readings(monkeypatch, build_wav):
    """Verifies rss_delta_mb is the RSS after the cold synthesis minus the RSS before the load."""
    wav = build_wav(frame_count=22050, sample_rate=22050)
    arrange(monkeypatch, [wav] * 2, [0.5, 0.25], rss_readings_mb=(100.0, 130.5))
    report = profile_melo(TEXT, repeats=1)
    assert report["rss_delta_mb"] == 30.5


def test_rss_delta_is_never_negative(monkeypatch, build_wav):
    """Verifies rss_delta_mb is clamped to 0.0 when the process shrank."""
    wav = build_wav(frame_count=22050, sample_rate=22050)
    arrange(monkeypatch, [wav] * 2, [0.5, 0.25], rss_readings_mb=(200.0, 150.0))
    report = profile_melo(TEXT, repeats=1)
    assert report["rss_delta_mb"] == 0.0


def test_acoustic_fields_describe_the_last_audio_produced(monkeypatch, build_wav):
    """Verifies sr_hz, peak, wav_kb, duration_s and wav_bytes come from the final synthesis."""
    first_wav = build_wav(frame_count=22050, sample_rate=22050, peak=16384)
    last_wav = build_wav(frame_count=8000, sample_rate=16000, peak=8192)
    arrange(monkeypatch, [first_wav] * 5 + [last_wav], [0.5] + [0.25] * 5)
    report = profile_melo(TEXT)
    assert len(last_wav) == 16044
    assert report["sr_hz"] == 16000
    assert report["peak"] == 0.25
    assert report["duration_s"] == 0.5
    assert report["wav_kb"] == 15.7
    assert report["wav_bytes"] == last_wav


def test_figures_are_rounded_to_their_reporting_precision(monkeypatch, build_wav):
    """Verifies load_ms, cold_first_s and peak are rounded to two, three and three places."""
    wav = build_wav(frame_count=22050, sample_rate=22050, peak=12345)
    arrange(monkeypatch, [wav, wav], [0.5, 0.25], load_milliseconds=1234.5678)
    report = profile_melo(TEXT, repeats=1)
    assert report["load_ms"] == 1234.57
    assert report["cold_first_s"] == 1.735
    assert report["peak"] == 0.377


def test_report_has_the_thirteen_fields_in_their_documented_order(
    monkeypatch, build_wav
):
    """Verifies the report keys come back in the order the benchmark tables expect."""
    wav = build_wav(frame_count=22050, sample_rate=22050)
    arrange(monkeypatch, [wav] * 2, [0.5, 0.25])
    report = profile_melo(TEXT, repeats=1)
    assert list(report) == REPORT_KEYS


def test_engine_is_melo_and_provider_is_the_requested_one(monkeypatch, build_wav):
    """Verifies the report names the melo engine and the provider that was asked for."""
    wav = build_wav(frame_count=22050, sample_rate=22050)
    arrange(monkeypatch, [wav] * 2, [0.5, 0.25])
    report = profile_melo(TEXT, repeats=1, provider="cuda")
    assert report["engine"] == "melo"
    assert report["provider"] == "cuda"
