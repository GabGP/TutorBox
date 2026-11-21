"""TimedCache: one build serves every caller within the window; a failed build is not kept."""

import threading
import time

import pytest

from core.system_health.cache import TimedCache


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class CountingBuild:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        return f"build {self.calls}"


def test_the_value_is_reused_until_the_window_has_passed():
    clock = FakeClock()
    cache: TimedCache[str] = TimedCache(2.0, clock)
    build = CountingBuild()

    first = cache.get(build)
    clock.now += 1.5  # exact binary steps keep the 2.0 s boundary exact
    second = cache.get(build)
    clock.now += 0.5
    third = cache.get(build)

    assert (first, second, third) == ("build 1", "build 1", "build 2")
    assert build.calls == 2


def test_the_window_counts_from_when_the_value_was_built():
    clock = FakeClock()
    cache: TimedCache[str] = TimedCache(2.0, clock)

    def slow_build() -> str:
        clock.now += 1.5  # the build itself takes 1.5 s
        return "slow"

    cache.get(slow_build)
    clock.now += 1.5  # 3.0 s after the build started, but 1.5 s after it was ready

    assert cache.get(CountingBuild()) == "slow"


def test_a_failed_build_is_not_kept():
    cache: TimedCache[str] = TimedCache(2.0, FakeClock())

    def failing_build() -> str:
        raise RuntimeError("the sensor is busy")

    with pytest.raises(RuntimeError):
        cache.get(failing_build)

    assert cache.get(CountingBuild()) == "build 1"


def test_callers_at_the_same_moment_share_one_build():
    cache: TimedCache[str] = TimedCache(2.0, FakeClock())
    build_started = threading.Event()
    release_build = threading.Event()
    builds: list[str] = []
    results: list[str] = []

    def slow_build() -> str:
        builds.append("built")
        build_started.set()
        release_build.wait(timeout=5)
        return "shared"

    first = threading.Thread(target=lambda: results.append(cache.get(slow_build)))
    first.start()
    assert build_started.wait(timeout=5)
    second = threading.Thread(target=lambda: results.append(cache.get(slow_build)))
    second.start()
    time.sleep(0.05)  # give the second caller time to reach the lock
    release_build.set()
    first.join(timeout=5)
    second.join(timeout=5)

    assert builds == ["built"]
    assert results == ["shared", "shared"]


def test_invalidate_makes_the_next_get_build_again():
    clock = FakeClock()
    cache: TimedCache[str] = TimedCache(2.0, clock)
    build = CountingBuild()
    cache.get(build)

    cache.invalidate()

    assert cache.get(build) == "build 2"
    assert build.calls == 2
