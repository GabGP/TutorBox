"""Mode 2 API: students chat with the tutor, teachers see who is using it."""

import pytest

from api.tutor.gate import TurnGate
from api.tutor.roster import TutorRoster
from api.tutor.service import get_roster, get_turn_gate, get_tutor
from core.llm import MockLLMClient
from core.security import token_digest
from modes.socratic import ConversationStore, SocraticTutor, TutorGateway
from src.main import app
from tests.conftest import auth_headers

MESSAGE = "/api/v1/tutor/message"
REWORDED = "¡Vamos! Queremos juntar 23 y 45. ¿Por dónde empiezas tú?"


@pytest.fixture
def tutor_mode(client, teacher_headers):
    resp = client.put("/api/v1/mode", json={"mode": "tutor"}, headers=teacher_headers)
    assert resp.status_code == 200


@pytest.fixture
def services():
    """A tutor with a mock model, a small gate and a fresh roster."""
    model = MockLLMClient([REWORDED, "¡Es 68! ¿Ves?"])
    tutor = SocraticTutor(TutorGateway(model, 1, 0.1), ConversationStore())
    gate = TurnGate(turns_per_minute=6)
    roster = TutorRoster()
    app.dependency_overrides[get_tutor] = lambda: tutor
    app.dependency_overrides[get_turn_gate] = lambda: gate
    app.dependency_overrides[get_roster] = lambda: roster
    yield roster
    app.dependency_overrides.clear()


def _say(client, headers, message):
    return client.post(MESSAGE, json={"message": message}, headers=headers)


def test_the_tutor_needs_a_login(staff_db, client):
    assert client.post(MESSAGE, json={"message": "hola"}).status_code == 401


def test_the_tutor_is_closed_outside_tutor_mode(student_headers, client, services):
    resp = _say(client, student_headers, "23 + 45")

    assert resp.status_code == 409
    assert "no está activo" in resp.json()["detail"]


def test_a_student_chats_and_every_turn_is_logged(
    staff_db, client, tutor_mode, services
):
    headers = auth_headers(client, "student1")

    first = _say(client, headers, "¿cuánto es 23 + 45?")
    assert first.status_code == 200
    assert first.json() == {
        "reply": REWORDED,
        "kind": "hint",
        "hint_level": 0,
        "used_model": True,
        "topic": None,
    }
    wrong = _say(client, headers, "70").json()  # the model now leaks: contained
    assert (wrong["kind"], wrong["hint_level"], wrong["used_model"]) == (
        "hint",
        1,
        False,
    )
    assert _say(client, headers, "68").json()["kind"] == "praise"

    _, conn = staff_db
    rows = conn.execute(
        "SELECT user_input, sympy_target_result, sympy_is_correct, "
        "containment_triggered FROM turn_logs ORDER BY id"
    ).fetchall()
    assert [tuple(row) for row in rows] == [
        ("¿cuánto es 23 + 45?", "68", None, 0),
        ("70", "68", 0, 1),
        ("68", "68", 1, 0),
    ]
    token = headers["Authorization"].removeprefix("Bearer ")
    logged = {row[0] for row in conn.execute("SELECT session_id FROM turn_logs")}
    assert logged == {token_digest(token)}  # the session's digest, never the token


def test_the_teacher_sees_who_is_using_the_tutor(
    staff_db, client, tutor_mode, services, teacher_headers
):
    student = auth_headers(client, "student1")
    assert client.post("/api/v1/tutor/ping", headers=student).json() == {"status": "ok"}
    _say(client, student, "7 por 8")
    _say(client, teacher_headers, "hola")  # teachers may try it; not listed

    resp = client.get("/api/v1/tutor/students", headers=teacher_headers)

    assert resp.status_code == 200
    assert resp.json()["students"] == [
        {
            "username": "student1",
            "online": True,
            "seconds_ago": 0,
            "turns": 1,
            "solved": 0,
            "problem": "7 × 8",
            "hint_level": 0,
        }
    ]
    assert client.get("/api/v1/tutor/students", headers=student).status_code == 403


def test_reset_forgets_the_problem(staff_db, client, tutor_mode, services):
    headers = auth_headers(client, "student1")
    _say(client, headers, "23 + 45")

    assert client.post("/api/v1/tutor/reset", headers=headers).json() == {
        "status": "ok"
    }

    assert _say(client, headers, "68").json()["kind"] == "orphan"
    assert services.snapshot()[0]["problem"] is None


def test_teachers_can_reset_and_ping_without_joining_the_roster(
    staff_db, client, services, teacher_headers
):
    assert (
        client.post("/api/v1/tutor/reset", headers=teacher_headers).status_code == 200
    )
    assert client.post("/api/v1/tutor/ping", headers=teacher_headers).status_code == 200
    assert services.snapshot() == []


def test_turns_are_rate_limited(staff_db, client, tutor_mode, services):
    headers = auth_headers(client, "student1")
    for _ in range(6):
        assert _say(client, headers, "hola").status_code == 200

    resp = _say(client, headers, "hola")

    assert resp.status_code == 429
    assert "rápido" in resp.json()["detail"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": "hola", "image": "data:image/png;base64,AAAA"},
        {"message": "x" * 2001},
    ],
)
def test_only_one_text_message_is_accepted(
    staff_db, client, tutor_mode, services, payload
):
    headers = auth_headers(client, "student1")

    assert client.post(MESSAGE, json=payload, headers=headers).status_code == 422


def test_the_services_are_built_once_per_process():
    for provider in (get_tutor, get_turn_gate, get_roster):
        provider.cache_clear()

    assert get_tutor() is get_tutor()
    assert isinstance(get_turn_gate(), TurnGate)
    assert isinstance(get_roster(), TutorRoster)

    for provider in (get_tutor, get_turn_gate, get_roster):
        provider.cache_clear()


def test_the_class_screen_gets_totals_without_names(staff_db, client, services):
    services.record(1, "ana", "23 + 45", 3, solved=False)  # stuck on the last hint
    services.record(2, "beto", "7 × 8", 1, solved=False)
    services.record(2, "beto", "7 × 8", 1, solved=True)

    resp = client.get("/api/v1/tutor/summary")  # no login: the wall screen

    assert resp.status_code == 200
    assert resp.json() == {"online": 2, "solved": 1, "need_help": 1}
