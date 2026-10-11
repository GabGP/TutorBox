"""Verifies WAV analysis reports duration, sample rate and normalised peak of PCM audio."""

import struct

import pytest

from tools.benchmark.tts.audio.wav_analysis import analyze_wav


def test_duration_is_frame_count_over_sample_rate(build_wav):
    """Verifies duration is the frame count divided by the sample rate."""
    duration, _sample_rate, _peak = analyze_wav(build_wav(frame_count=2205))
    assert duration == pytest.approx(0.1)


def test_sample_rate_is_reported_from_the_header(build_wav):
    """Verifies the sample rate is reported as the header states it, such as 24000 Hz."""
    duration, sample_rate, _peak = analyze_wav(build_wav(sample_rate=24000))
    assert sample_rate == 24000
    assert duration == pytest.approx(2205 / 24000)


def test_sixteen_bit_peak_is_normalised_by_32768(build_wav):
    """Verifies a 16384 sample peak is reported as 0.5 of full scale."""
    _duration, _sample_rate, peak = analyze_wav(build_wav(peak=16384))
    assert peak == 0.5


def test_zero_frame_wav_has_zero_duration_and_peak(build_wav):
    """Verifies a WAV without frames reports zero duration and peak but keeps its rate."""
    assert analyze_wav(build_wav(frame_count=0)) == (0.0, 22050, 0.0)


def test_zero_sample_rate_gives_zero_duration_but_keeps_the_peak(build_wav):
    """Verifies a header with a zero sample rate reports zero duration and still measures the peak."""
    wav_bytes = bytearray(build_wav(peak=16384))
    # The wave writer refuses a zero rate, so the canonical header's rate field
    # (bytes 24 to 27, little-endian) is zeroed after the file is written.
    wav_bytes[24:28] = struct.pack("<I", 0)
    duration, sample_rate, peak = analyze_wav(bytes(wav_bytes))
    assert duration == 0.0
    assert sample_rate == 0
    assert peak == 0.5


def test_eight_bit_wav_reports_duration_and_rate_but_no_peak(build_wav):
    """Verifies non-16-bit audio keeps its duration and rate, with the peak left at zero."""
    duration, sample_rate, peak = analyze_wav(build_wav(sample_width=1))
    assert duration == pytest.approx(0.1)
    assert sample_rate == 22050
    assert peak == 0.0


def test_stereo_duration_counts_frames_not_samples(build_wav):
    """Verifies stereo duration counts frames, so two channels do not double the length."""
    duration, _sample_rate, peak = analyze_wav(build_wav(channel_count=2))
    assert duration == pytest.approx(0.1)
    assert peak == 0.5
