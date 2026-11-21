"""Quiz model endpoints (POST /quiz/model/load|unload) and the generate endpoint's model marking."""

import pytest
from fastapi.testclient import TestClient

from api.quiz.dependencies import get_quiz_generator
from core.llm import MockLLMClient
from core.llm.residency import get_model_residency
from core.llm.residency.models import ResidencyError
from modes.quiz.generation.generator import QuizQuestionGenerator
from src.main import app
from tests.api.quiz.test_generate import VALID_LLM_OUTPUT
from tests.conftest import auth_headers
from tests.core.llm.residency.fakes import (
    QUIZ_MODEL,
    FakeCountdowns,
    FakeResidencyClient,
    build_fake_manager,
)

GENERATE_BODY = {
    "topic": "arithmetic",
    "subconcept": "addition_subtraction",
    "save_to_bank": False,
}


@pytest.fixture
def residency():
    client = FakeResidencyClient()
    countdowns = FakeCountdowns()
    manager = build_fake_manager(client, countdowns)
    app.dependency_overrides[get_model_residency] = lambda: manager
    yield client, countdowns
    app.dependency_overrides.pop(get_model_residency, None)


@pytest.fixture
def scripted_generator():
    llm = MockLLMClient([VALID_LLM_OUTPUT])
    app.dependency_overrides[get_quiz_generator] = lambda: QuizQuestionGenerator(
        llm_client=llm
    )
    yield
    app.dependency_overrides.pop(get_quiz_generator, None)


def test_teacher_loads_the_quiz_model(staff_db, client: TestClient, residency):
    client_fake, _ = residency
    headers = auth_headers(client, "teacher1")

    resp = client.post("/api/v1/quiz/model/load", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["model"] == QUIZ_MODEL
    assert resp.json()["action"] == "loaded"
    assert client_fake.called() == [("load", QUIZ_MODEL)]


def test_admin_unloads_the_quiz_model(staff_db, client: TestClient, residency):
    client_fake, countdowns = residency
    headers = auth_headers(client, "admin1")
    client.post("/api/v1/quiz/model/load", headers=headers)

    resp = client.post("/api/v1/quiz/model/unload", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["action"] == "unloaded"
    assert client_fake.called()[-1] == ("unload", QUIZ_MODEL)
    assert countdowns.latest.cancelled is True


def test_students_cannot_load_or_unload_the_quiz_model(
    staff_db, client: TestClient, residency
):
    client_fake, _ = residency
    headers = auth_headers(client, "student1")

    assert client.post("/api/v1/quiz/model/load", headers=headers).status_code == 403
    assert client.post("/api/v1/quiz/model/unload", headers=headers).status_code == 403
    assert client_fake.calls == []


def test_anonymous_callers_are_refused(client: TestClient, residency):
    assert client.post("/api/v1/quiz/model/load").status_code == 401
    assert client.post("/api/v1/quiz/model/unload").status_code == 401


def test_a_failing_server_is_reported_not_raised(
    staff_db, client: TestClient, residency
):
    client_fake, _ = residency
    client_fake.load_error = ResidencyError("Ollama is unreachable: refused")
    headers = auth_headers(client, "teacher1")

    resp = client.post("/api/v1/quiz/model/load", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["action"] == "failed"


def test_generation_marks_the_model_in_use_and_leaves_it_loaded(
    staff_db, client: TestClient, residency, scripted_generator
):
    client_fake, countdowns = residency
    headers = auth_headers(client, "teacher1")

    resp = client.post("/api/v1/quiz/generate", headers=headers, json=GENERATE_BODY)

    assert resp.status_code == 200
    # Loaded on demand (the batch did not call /model/load), then left for the batch to release.
    assert client_fake.called() == [("load", QUIZ_MODEL)]
    assert countdowns.latest.started is True
    assert countdowns.latest.cancelled is False


def test_generation_still_answers_when_the_model_cannot_be_loaded(
    staff_db, client: TestClient, residency, scripted_generator
):
    client_fake, _ = residency
    client_fake.load_error = ResidencyError("HTTP 500")
    headers = auth_headers(client, "teacher1")

    resp = client.post("/api/v1/quiz/generate", headers=headers, json=GENERATE_BODY)

    assert resp.status_code == 200


def test_the_process_manager_is_switched_off_in_tests(staff_db, client: TestClient):
    assert (
        get_model_residency().enabled is False
    )  # conftest sets SLM_MANAGE_RESIDENCY=false
