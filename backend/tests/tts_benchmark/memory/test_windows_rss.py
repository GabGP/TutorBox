"""Verifies the Windows working-set reader and its None results on failure."""

import ctypes
from types import SimpleNamespace

from tools.benchmark.tts.memory import windows_rss
from tools.benchmark.tts.shared.units import BYTES_PER_MB


def megabytes_as_bytes(megabytes: float) -> int:
    """Converts megabytes to a whole byte count, as the Windows API reports it."""
    return int(megabytes * BYTES_PER_MB)


class WindowsApiUnavailableError(OSError):
    """Raised by the fake windll below to mimic a broken Windows API."""


class ExplodingWindll:
    """Raises on any attribute access, as a broken ctypes.windll would."""

    def __getattr__(self, attribute_name: str) -> object:
        raise WindowsApiUnavailableError


def make_fake_windll(working_set_bytes: int, call_succeeds: bool) -> SimpleNamespace:
    """Builds a windll stand-in whose GetProcessMemoryInfo reports a fixed working set."""

    def get_process_memory_info(process_handle, counters_reference, counters_size):
        counters_reference._obj.WorkingSetSize = working_set_bytes
        return 1 if call_succeeds else 0

    def get_current_process():
        return 1

    return SimpleNamespace(
        psapi=SimpleNamespace(GetProcessMemoryInfo=get_process_memory_info),
        kernel32=SimpleNamespace(GetCurrentProcess=get_current_process),
    )


def test_working_set_is_reported_in_megabytes(monkeypatch):
    """Verifies a successful GetProcessMemoryInfo call returns the working set in MB."""
    fake_windll = make_fake_windll(megabytes_as_bytes(3), call_succeeds=True)
    monkeypatch.setattr(ctypes, "windll", fake_windll, raising=False)
    assert windows_rss.working_set_megabytes() == 3.0


def test_api_call_returning_false_gives_none(monkeypatch):
    """Verifies a GetProcessMemoryInfo call that returns false gives None."""
    fake_windll = make_fake_windll(megabytes_as_bytes(3), call_succeeds=False)
    monkeypatch.setattr(ctypes, "windll", fake_windll, raising=False)
    assert windows_rss.working_set_megabytes() is None


def test_exception_from_windll_gives_none(monkeypatch):
    """Verifies an exception raised while reaching the Windows API gives None."""
    monkeypatch.setattr(ctypes, "windll", ExplodingWindll(), raising=False)
    assert windows_rss.working_set_megabytes() is None


def test_missing_windll_gives_none(monkeypatch):
    """Verifies a Python without ctypes.windll, such as on Linux, gives None."""
    monkeypatch.delattr(ctypes, "windll", raising=False)
    assert windows_rss.working_set_megabytes() is None
