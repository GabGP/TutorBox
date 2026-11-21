"""PUT /api/v1/mode moves the tutor model with the mode (src/api/mode.py)."""

import pytest

from core.llm.residency import get_model_residency
from core.llm.residency.models import ResidencyError
from src.main import app
from tests.api.session.test_session_endpoints import _seed_quiz_questions
from tests.conftest import auth_headers
from tests.core.llm.residency.fakes import (
    TUTOR_MODEL,
    FakeCountdowns,
    FakeResidencyClient,
    build_fake_manager,
)


@pytest.fixture
def residency(monkeypatch: pytest.MonkeyPatch):
    client = FakeResidencyClient()
    manager = build_fake_manager(client, FakeCountdowns())
    app.dependency_overrides[get_model_residency] = lambda: manager
    yield client
    app.dependency_overrides.pop(get_model_residency, None)


def _start_live_quiz(client, conn, headers) -> None:
    payload = {
        "title": "Clase",
        "topic": "arithmetic",
        "question_ids": _seed_quiz_questions(conn),
    }
    session_id = client.post("/api/v1/session", json=payload, headers=headers).json()[
        "id"
    ]
    assert (
        client.post(f"/api/v1/session/{session_id}/start", headers=headers).status_code
        == 200
    )


def test_switching_to_tutor_answers_with_the_model_result(staff_db, client, residency):
    headers = auth_headers(client, "teacher1")

    resp = client.put("/api/v1/mode", json={"mode": "tutor"}, headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "tutor"
    assert body["model"]["model"] == TUTOR_MODEL
    assert body["model"]["action"] == "loaded"
    assert body["model"]["duration_ms"] == pytest.approx(3200.0)
    assert residency.called() == [("load", TUTOR_MODEL)]


def test_leaving_tutor_unloads_the_tutor_model(staff_db, client, residency):
    headers = auth_headers(client, "teacher1")
    client.put("/api/v1/mode", json={"mode": "tutor"}, headers=headers)

    body = client.put("/api/v1/mode", json={"mode": "apps"}, headers=headers).json()

    assert body["model"]["action"] == "unloaded"
    assert residency.called()[-1] == ("unload", TUTOR_MODEL)


def test_an_unreachable_server_still_saves_the_mode(staff_db, client, residency):
    residency.load_error = ResidencyError("Ollama is unreachable: refused")
    headers = auth_headers(client, "teacher1")

    resp = client.put("/api/v1/mode", json={"mode": "tutor"}, headers=headers)

    assert resp.status_code == 200
    assert resp.json()["model"]["action"] == "failed"
    assert client.get("/api/v1/mode").json() == {"mode": "tutor"}


def test_refused_switch_during_a_live_round_keeps_the_model(
    staff_db, client, residency
):
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    _start_live_quiz(client, conn, headers)

    resp = client.put("/api/v1/mode", json={"mode": "tutor"}, headers=headers)

    assert resp.status_code == 409
    assert residency.calls == []
    assert client.get("/api/v1/mode").json() == {"mode": "quiz"}


def test_students_cannot_switch_and_the_model_is_not_touched(
    staff_db, client, residency
):
    headers = auth_headers(client, "student2")

    resp = client.put("/api/v1/mode", json={"mode": "tutor"}, headers=headers)

    assert resp.status_code == 403
    assert residency.calls == []
