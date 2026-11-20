"""Tests for stopping POST /api/v1/quiz/generate when the teacher leaves."""

import asyncio
import threading
from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

import api.quiz.generate as generate_module
from api.quiz import disconnect_watch
from api.quiz.dependencies import get_quiz_generator
from core.llm import MockLLMClient
from modes.quiz.generation.generator import QuizQuestionGenerator
from src.main import app
from tests.api.quiz.test_generate import VALID_LLM_OUTPUT
from tests.conftest import auth_headers

GENERATE_BODY = {
    "topic": "arithmetic",
    "subconcept": "addition_subtraction",
    "save_to_bank": True,
}


@pytest.fixture
def mock_llm() -> Iterator[MockLLMClient]:
    """Routes the generator to a mock LLM that always returns a valid question."""
    llm = MockLLMClient([VALID_LLM_OUTPUT])
    app.dependency_overrides[get_quiz_generator] = lambda: QuizQuestionGenerator(
        llm_client=llm
    )
    yield llm
    app.dependency_overrides.pop(get_quiz_generator, None)


def _client_leaves_after(checks_before_leaving: int):
    """Replaces the watcher with one whose client leaves after N checks."""
    checks_seen = 0

    def client_has_left() -> bool:
        nonlocal checks_seen
        checks_seen += 1
        return checks_seen > checks_before_leaving

    async def fake_run(_request, blocking_work: Callable[[Callable[[], bool]], object]):
        return blocking_work(client_has_left)

    return fake_run


def test_client_gone_before_first_attempt_skips_llm(
    staff_db, client: TestClient, mock_llm: MockLLMClient, monkeypatch
):
    """A teacher who already left gets 499 and the LLM is never asked."""
    monkeypatch.setattr(
        generate_module, "run_until_disconnected", _client_leaves_after(0)
    )
    headers = auth_headers(client, "teacher1", "1234")
    response = client.post("/api/v1/quiz/generate", headers=headers, json=GENERATE_BODY)

    assert response.status_code == 499
    assert mock_llm.call_history == []


def test_question_finished_after_stop_is_not_saved(
    staff_db, client: TestClient, mock_llm: MockLLMClient, monkeypatch
):
    """The teacher leaves during the LLM call: the question never reaches the bank."""
    _, conn = staff_db
    count_questions = "SELECT COUNT(*) FROM quiz_questions"
    questions_before = conn.execute(count_questions).fetchone()[0]
    monkeypatch.setattr(
        generate_module, "run_until_disconnected", _client_leaves_after(1)
    )
    headers = auth_headers(client, "teacher1", "1234")
    response = client.post("/api/v1/quiz/generate", headers=headers, json=GENERATE_BODY)

    assert response.status_code == 499
    assert len(mock_llm.call_history) == 1
    questions_after = conn.execute(count_questions).fetchone()[0]
    count_logs = "SELECT COUNT(*) FROM quiz_generation_logs"
    logged_count = conn.execute(count_logs).fetchone()[0]
    assert (questions_after, logged_count) == (questions_before, 0)


class _RequestThatLeaves:
    """Fake request that reports a disconnect from the Nth poll on."""

    def __init__(self, polls_before_leaving: int) -> None:
        self.polls_before_leaving = polls_before_leaving
        self.polls_seen = 0

    async def is_disconnected(self) -> bool:
        self.polls_seen += 1
        return self.polls_seen > self.polls_before_leaving


def test_watcher_flags_work_when_client_leaves(monkeypatch):
    """Blocking work sees `client_has_left()` turn True once the client leaves."""
    monkeypatch.setattr(disconnect_watch, "DISCONNECT_POLL_SECONDS", 0.01)
    work_may_finish = threading.Event()

    def wait_for_client_to_leave(client_has_left: Callable[[], bool]) -> str:
        while not client_has_left():
            work_may_finish.wait(0.01)
        return "stopped"

    request = _RequestThatLeaves(polls_before_leaving=2)
    result = asyncio.run(
        disconnect_watch.run_until_disconnected(request, wait_for_client_to_leave)
    )

    assert result == "stopped"
    assert request.polls_seen == 3


def test_watcher_returns_result_while_client_stays():
    """Work that finishes first returns its result and the flag stays False."""
    flag_seen: list[bool] = []

    def quick_work(client_has_left: Callable[[], bool]) -> int:
        flag_seen.append(client_has_left())
        return 42

    request = _RequestThatLeaves(polls_before_leaving=1000)
    result = asyncio.run(disconnect_watch.run_until_disconnected(request, quick_work))

    assert result == 42
    assert flag_seen == [False]
