"""GET /api/v1/system/health: staff only, one snapshot of the appliance, nulls when files are missing."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.system_health.cpu import CpuMonitor
from core.system_health.factory import get_system_health_service
from core.system_health.models import ModelReading
from core.system_health.service import SystemHealthService
from src.main import app
from tests.core.system_health.fake_host import FakeHost, write_board

HEALTH_URL = "/api/v1/system/health"


def make_service(root: Path) -> SystemHealthService:
    return SystemHealthService(
        root=root,
        data_directory=root,
        models_in_memory=lambda: [ModelReading(name="qwen2.5:3b", gpu_percent=100)],
        voices_loaded=lambda: ["piper"],
        cpu_monitor=CpuMonitor(
            root, first_pause_seconds=0, sleep=lambda _seconds: None
        ),
    )


@pytest.fixture
def board_service(tmp_path: Path) -> Iterator[SystemHealthService]:
    write_board(FakeHost(tmp_path))
    service = make_service(tmp_path)
    app.dependency_overrides[get_system_health_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_system_health_service, None)


def test_the_health_panel_needs_a_session(staff_db, client: TestClient, board_service):
    assert client.get(HEALTH_URL).status_code == 401


def test_a_student_cannot_read_the_health_panel(
    staff_db, client: TestClient, board_service, student_headers
):
    response = client.get(HEALTH_URL, headers=student_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions."


def test_a_teacher_gets_every_reading(
    staff_db, client: TestClient, board_service, teacher_headers
):
    response = client.get(HEALTH_URL, headers=teacher_headers)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "sampled_at",
        "cpu",
        "memory",
        "gpu",
        "temperatures",
        "power",
        "disk",
        "uptime_seconds",
        "load_average",
        "models",
        "voices",
    }
    assert body["gpu"]["load_percent"] == 99.8
    assert body["memory"]["status"] == "ok"
    assert body["temperatures"][0]["zone"] == "cpu-thermal"
    assert body["power"][0] == {"rail": "VDD_IN", "milliwatts": 5981}
    assert body["models"] == [{"name": "qwen2.5:3b", "gpu_percent": 100}]
    assert body["voices"] == ["piper"]


def test_an_admin_can_read_the_health_panel_too(
    staff_db, client: TestClient, board_service, admin_headers
):
    assert client.get(HEALTH_URL, headers=admin_headers).status_code == 200


def test_a_machine_without_these_files_still_answers_with_nulls(
    staff_db, client: TestClient, tmp_path, teacher_headers
):
    empty_root = tmp_path / "pc"
    empty_root.mkdir()
    app.dependency_overrides[get_system_health_service] = lambda: make_service(
        empty_root
    )
    try:
        response = client.get(HEALTH_URL, headers=teacher_headers)
    finally:
        app.dependency_overrides.pop(get_system_health_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["memory"] is None
    assert body["gpu"] is None
    assert body["cpu"]["status"] == "unknown"
    assert body["temperatures"] == []
