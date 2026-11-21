"""MemoryReleaser: runs every phase, waits for the RAM to settle, reports, and never raises."""

import time

import pytest

from core.llm.residency.models import ResidencyAction
from core.system_health import memory_release
from core.system_health.memory_release import MemoryReleaser, ReleasePhase
from core.system_health.release_report import ReleaseAction, ReleaseKind


class AvailableMemory:
    """Hands out the readings in order: before the release, then after it."""

    def __init__(self, *readings: float | None) -> None:
        self.readings = list(readings)

    def __call__(self) -> float | None:
        return self.readings.pop(0)


def action(
    target: str, kind: ReleaseKind = "voice", result: ResidencyAction = "unloaded"
) -> ReleaseAction:
    return ReleaseAction(target=target, kind=kind, action=result)


@pytest.fixture
def pauses(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []
    monkeypatch.setattr(time, "sleep", recorded.append)
    return recorded


def test_the_report_has_the_ram_before_and_after_and_every_action(pauses):
    invalidations: list[bool] = []
    releaser = MemoryReleaser(
        phases=[
            ReleasePhase(
                "modelos", "quiz_model", lambda: [action("qwen2.5:3b", "quiz_model")]
            ),
            ReleasePhase("voces", "voice", lambda: [action("voz piper")]),
        ],
        read_available_mb=AvailableMemory(1000.0, 3300.5),
        invalidate_snapshot=lambda: invalidations.append(True),
    )

    report = releaser.release()

    assert report.available_before_mb == 1000.0
    assert report.available_after_mb == 3300.5
    assert report.freed_mb == 2300.5
    assert [item.target for item in report.actions] == ["qwen2.5:3b", "voz piper"]
    assert pauses == [memory_release.RELEASE_SETTLE_SECONDS]
    assert invalidations == [True]


def test_a_failing_phase_is_reported_and_the_others_still_run(pauses):
    def broken() -> list[ReleaseAction]:
        raise RuntimeError("the residency client is gone")

    releaser = MemoryReleaser(
        phases=[
            ReleasePhase("modelos", "quiz_model", broken),
            ReleasePhase(
                "heap del proceso",
                "backend_heap",
                lambda: [action("heap", "backend_heap")],
            ),
        ],
        read_available_mb=AvailableMemory(1000.0, 1200.0),
        invalidate_snapshot=lambda: None,
        settle_seconds=0.0,
    )

    report = releaser.release()

    assert [(item.target, item.kind, item.action) for item in report.actions] == [
        ("modelos", "quiz_model", "failed"),
        ("heap", "backend_heap", "unloaded"),
    ]
    assert report.actions[0].detail == "the residency client is gone"


def test_an_unreadable_memory_gives_no_freed_amount(pauses):
    releaser = MemoryReleaser(
        phases=[],
        read_available_mb=AvailableMemory(None, 2000.0),
        invalidate_snapshot=lambda: None,
        settle_seconds=0.0,
    )

    report = releaser.release()

    assert report.available_before_mb is None
    assert report.freed_mb is None
    assert report.actions == []


def test_a_release_that_frees_nothing_can_report_a_negative_amount(pauses):
    releaser = MemoryReleaser(
        phases=[],
        read_available_mb=AvailableMemory(2000.0, 1990.0),
        invalidate_snapshot=lambda: None,
        settle_seconds=0.0,
    )

    assert releaser.release().freed_mb == -10.0
