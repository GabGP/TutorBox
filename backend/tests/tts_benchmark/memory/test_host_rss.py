"""Verifies the host RSS reader: the psutil process tree first, then the Windows fallback."""

import sys
from types import SimpleNamespace

from tools.benchmark.tts.memory import host_rss
from tools.benchmark.tts.shared.units import BYTES_PER_MB


class FakeNoSuchProcessError(Exception):
    """Mirrors psutil.NoSuchProcess for a child that exited before it was read."""


class FakeAccessDeniedError(Exception):
    """Mirrors psutil.AccessDenied for a child this process may not inspect."""


class FakeProcess:
    """Stands in for psutil.Process with a fixed RSS and a list of children."""

    def __init__(self, rss_megabytes: float, children: tuple = ()) -> None:
        self._rss_bytes = int(rss_megabytes * BYTES_PER_MB)
        self._children = list(children)

    def memory_info(self) -> SimpleNamespace:
        return SimpleNamespace(rss=self._rss_bytes)

    def children(self, recursive: bool) -> list:
        return self._children


class ChildThatVanishes:
    """Stands in for a child process that exits before its memory is read."""

    def memory_info(self) -> SimpleNamespace:
        raise FakeNoSuchProcessError


class ChildOwnedByAnotherUser:
    """Stands in for a child process whose memory the parent may not read."""

    def memory_info(self) -> SimpleNamespace:
        raise FakeAccessDeniedError


def install_fake_psutil(monkeypatch, process: FakeProcess) -> None:
    """Installs a psutil stand-in whose Process() returns the given fake process."""
    fake_psutil = SimpleNamespace(
        Process=lambda: process,
        NoSuchProcess=FakeNoSuchProcessError,
        AccessDenied=FakeAccessDeniedError,
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)


def use_platform(monkeypatch, platform_name: str) -> None:
    """Replaces the sys reference seen by the host_rss module."""
    monkeypatch.setattr(host_rss, "sys", SimpleNamespace(platform=platform_name))


def test_psutil_total_sums_the_process_and_its_children(monkeypatch):
    """Verifies the default reading adds the RSS of every child to the parent's."""
    children = (FakeProcess(20.0), FakeProcess(30.0))
    install_fake_psutil(monkeypatch, FakeProcess(100.0, children))
    assert host_rss.get_host_rss_mb() == 150.0


def test_include_children_false_reports_only_the_process(monkeypatch):
    """Verifies include_children=False ignores the child processes entirely."""
    install_fake_psutil(monkeypatch, FakeProcess(100.0, (FakeProcess(20.0),)))
    assert host_rss.get_host_rss_mb(include_children=False) == 100.0


def test_child_that_vanishes_keeps_the_parent_value(monkeypatch):
    """Verifies a child exiting mid-scan leaves the parent's RSS as the total."""
    install_fake_psutil(monkeypatch, FakeProcess(100.0, (ChildThatVanishes(),)))
    assert host_rss.get_host_rss_mb() == 100.0


def test_child_access_denied_keeps_the_parent_value(monkeypatch):
    """Verifies a child the process may not inspect leaves the parent's RSS as the total."""
    install_fake_psutil(monkeypatch, FakeProcess(100.0, (ChildOwnedByAnotherUser(),)))
    assert host_rss.get_host_rss_mb() == 100.0


def test_missing_psutil_on_windows_uses_the_working_set(monkeypatch):
    """Verifies that without psutil, Windows reports the working-set helper's value."""
    monkeypatch.setitem(sys.modules, "psutil", None)
    use_platform(monkeypatch, "win32")
    monkeypatch.setattr(host_rss, "working_set_megabytes", lambda: 42.0)
    assert host_rss.get_host_rss_mb() == 42.0


def test_missing_psutil_on_windows_with_no_working_set_gives_zero(monkeypatch):
    """Verifies a Windows working-set helper returning None leads to 0.0."""
    monkeypatch.setitem(sys.modules, "psutil", None)
    use_platform(monkeypatch, "win32")
    monkeypatch.setattr(host_rss, "working_set_megabytes", lambda: None)
    assert host_rss.get_host_rss_mb() == 0.0


def test_missing_psutil_on_linux_gives_zero_without_the_windows_helper(monkeypatch):
    """Verifies that off Windows the Windows helper is never consulted."""
    consulted: list[str] = []

    def record_windows_helper():
        consulted.append("working_set_megabytes")
        return 42.0

    monkeypatch.setitem(sys.modules, "psutil", None)
    use_platform(monkeypatch, "linux")
    monkeypatch.setattr(host_rss, "working_set_megabytes", record_windows_helper)
    assert host_rss.get_host_rss_mb() == 0.0
    assert consulted == []


def test_psutil_without_process_falls_through_to_the_windows_helper(monkeypatch):
    """Verifies a psutil module lacking Process (AttributeError) falls through."""
    fake_psutil = SimpleNamespace(
        NoSuchProcess=FakeNoSuchProcessError, AccessDenied=FakeAccessDeniedError
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    use_platform(monkeypatch, "win32")
    monkeypatch.setattr(host_rss, "working_set_megabytes", lambda: 7.0)
    assert host_rss.get_host_rss_mb() == 7.0
