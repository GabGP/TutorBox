"""Integration tests for the public session state consumed by Pilas clients."""

from core.db.session_repository import update_quiz_session_status
from tests.api.session.test_session_endpoints import _seed_quiz_questions
from tests.conftest import auth_headers


def _create(client, conn, title="Clase", **extra) -> str:
    payload = {
        "title": title,
        "topic": "arithmetic",
        "question_ids": _seed_quiz_questions(conn),
        **extra,
    }
    resp = client.post(
        "/api/v1/session", json=payload, headers=auth_headers(client, "teacher1")
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_current_returns_404_when_no_session(staff_db, client):
    resp = client.get("/api/v1/session/current")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "No active session."


def test_current_is_public_and_picks_newest_open_session(staff_db, client):
    _, conn = staff_db
    older = _create(client, conn, "Ayer")
    newer = _create(client, conn, "Hoy")

    resp = client.get("/api/v1/session/current")  # no auth header on purpose
    assert resp.status_code == 200
    assert resp.json()["id"] == newer

    # A completed session is never "current"; the older open one takes over.
    update_quiz_session_status(conn, newer, "completed")
    conn.commit()
    assert client.get("/api/v1/session/current").json()["id"] == older

    update_quiz_session_status(conn, older, "completed")
    conn.commit()
    assert client.get("/api/v1/session/current").status_code == 404


def test_public_state_gates_question_and_result_by_phase(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    student = auth_headers(client, "student1")
    session_id = _create(client, conn, duration_seconds=20)

    lobby = client.get(f"/api/v1/session/{session_id}").json()["current_round"]
    assert lobby["status"] == "pending"
    assert lobby["question"] is None and lobby["result"] is None
    assert lobby["votes_cast"] == 0

    client.post(f"/api/v1/session/{session_id}/start", headers=teacher)
    body = client.get(f"/api/v1/session/{session_id}").text
    assert "correct_option" not in body and "explanation" not in body
    open_round = client.get(f"/api/v1/session/{session_id}").json()["current_round"]
    assert open_round["question"]["question_text"] == "2 + 3?"
    assert open_round["question"]["options"]["A"] == "5"
    assert open_round["duration_seconds"] == 20
    assert open_round["result"] is None

    vote = client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "B", "transport_type": "web"},
        headers=student,
    )
    assert vote.status_code == 200
    assert (
        client.get(f"/api/v1/session/{session_id}").json()["current_round"][
            "votes_cast"
        ]
        == 1
    )

    reveal = client.post(f"/api/v1/session/{session_id}/reveal", headers=teacher)
    assert reveal.status_code == 200
    revealed = client.get(f"/api/v1/session/{session_id}").json()["current_round"]
    assert revealed["status"] == "revealed"
    assert revealed["result"]["tally"] == reveal.json()["tally"]
    assert revealed["result"]["decision"] == reveal.json()["decision"]
    assert revealed["result"]["tally"]["correct_option"] == "A"
    assert revealed["result"]["explanations"]["B"] == "Sumaste 1 de mas."
    assert set(revealed["result"]["explanations"]) == {"B", "C", "D"}
    # /current serves the same enriched payload to unauthenticated clients.
    assert client.get("/api/v1/session/current").json()["current_round"] == revealed


def test_pilas_pages_are_served_by_the_backend(staff_db, client):
    for path in ("/maestro/", "/alumno/", "/pantalla/"):
        resp = client.get(path)
        assert resp.status_code == 200, path
        assert resp.headers["content-type"].startswith("text/html")
    assert client.get("/static/tb.css").status_code == 200
    assert client.get("/", follow_redirects=False).headers["location"] == "/alumno/"
    # Mounting pages must not change API behaviour for unknown paths.
    assert client.get("/api/v1/session/does-not-exist").json() == {
        "detail": "Session 'does-not-exist' not found."
    }
    assert client.get("/api/v1/nope").json() == {"detail": "Not Found"}
