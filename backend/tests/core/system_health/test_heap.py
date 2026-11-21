"""heap: gc, then malloc_trim(0) through glibc; every platform gets an answer and nothing raises."""

import sys

from core.system_health import heap


class FakeLibc:
    def __init__(self, released: int) -> None:
        self.released = released
        self.trim_arguments: list[int] = []

    def malloc_trim(self, pad: int) -> int:
        self.trim_arguments.append(pad)
        return self.released


class NoTrimLibc:
    """A C library without malloc_trim (musl, or a non-glibc system)."""


def test_on_linux_the_free_heap_is_trimmed_and_reported(monkeypatch):
    libc = FakeLibc(released=1)
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(heap.ctypes, "CDLL", lambda _name: libc)

    action = heap.trim_backend_heap()

    assert libc.trim_arguments == [0]
    assert (action.kind, action.action) == ("backend_heap", "unloaded")
    assert action.detail == "malloc_trim returned free pages"


def test_nothing_to_return_is_still_a_clean_result(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(heap.ctypes, "CDLL", lambda _name: FakeLibc(released=0))

    action = heap.trim_backend_heap()

    assert action.action == "unloaded"
    assert action.detail == "no free pages to return"


def test_garbage_collection_runs_on_every_platform(monkeypatch):
    collections: list[bool] = []
    monkeypatch.setattr(heap.gc, "collect", lambda: collections.append(True) or 0)
    monkeypatch.setattr(sys, "platform", "win32")

    action = heap.trim_backend_heap()

    assert collections == [True]
    assert action.action == "unsupported"


def test_a_missing_c_library_fails_without_raising(monkeypatch):
    def no_library(_name: str):
        raise OSError("libc.so.6: cannot open shared object file")

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(heap.ctypes, "CDLL", no_library)

    action = heap.trim_backend_heap()

    assert action.action == "failed"
    assert "cannot open shared object" in (action.detail or "")


def test_a_library_without_malloc_trim_fails_without_raising(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(heap.ctypes, "CDLL", lambda _name: NoTrimLibc())

    action = heap.trim_backend_heap()

    assert action.action == "failed"
