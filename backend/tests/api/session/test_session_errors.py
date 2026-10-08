"""Negative and error branch integration tests for quiz session REST API."""

from core.db.question_repository import create_question
from modes.quiz.contracts.models import DistractorDetail, QuizQuestionCreate
from tests.conftest import auth_headers


def _seed_question(conn) -> str:
    qid = create_question(
        conn,
        QuizQuestionCreate(
            topic="arithmetic",
            subconcept="addition",
            question_text="1 + 1?",
            options={"A": "2", "B": "3", "C": "4", "D": "0"},
            correct_option="A",
            distractors={
                "B": DistractorDetail(
                    misconception="add1", explanation="Sumaste de mas."
                ),
                "C": DistractorDetail(
                    misconception="add2", explanation="Sumaste 2 de mas."
                ),
                "D": DistractorDetail(misconception="sub", explanation="Restaste."),
            },
        ),
    )
    conn.commit()
    return qid


def test_missing_session_endpoints_return_404(staff_db, client):
    teacher_headers = auth_headers(client, "teacher1")
    s1_headers = auth_headers(client, "student1")

    # Missing session across host and report routes
    assert (
        client.get(
            "/api/v1/session/missing_id/report", headers=teacher_headers
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/session/missing_id/start", headers=teacher_headers
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/session/missing_id/close", headers=teacher_headers
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/session/missing_id/reveal", headers=teacher_headers
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/session/missing_id/next", headers=teacher_headers
        ).status_code
        == 404
    )

    # Missing session on vote route
    vote_resp = client.post(
        "/api/v1/session/missing_id/vote",
        json={"selected_option": "A"},
        headers=s1_headers,
    )
    assert vote_resp.status_code == 404


def test_invalid_round_state_transitions_return_409(staff_db, client):
    _, conn = staff_db
    qid = _seed_question(conn)
    teacher_headers = auth_headers(client, "teacher1")
    s1_headers = auth_headers(client, "student1")

    create_resp = client.post(
        "/api/v1/session",
        json={
            "title": "Error State Test",
            "topic": "arithmetic",
            "question_ids": [qid],
        },
        headers=teacher_headers,
    )
    session_id = create_resp.json()["id"]

    # In lobby state (round is pending), close and reveal raise 409
    assert (
        client.post(
            f"/api/v1/session/{session_id}/close", headers=teacher_headers
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/api/v1/session/{session_id}/reveal", headers=teacher_headers
        ).status_code
        == 409
    )

    # Start session -> open round
    client.post(f"/api/v1/session/{session_id}/start", headers=teacher_headers)
    # Close round
    client.post(f"/api/v1/session/{session_id}/close", headers=teacher_headers)

    # Voting on a closed round returns 409
    closed_vote_resp = client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "A"},
        headers=s1_headers,
    )
    assert closed_vote_resp.status_code == 409


def test_next_only_moves_on_from_a_revealed_round(staff_db, client):
    """A second tap on "Siguiente" cannot skip a question; bad states are 409."""
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    qid = _seed_question(conn)
    created = client.post(
        "/api/v1/session",
        json={
            "title": "Doble toque",
            "topic": "arithmetic",
            "question_ids": [qid, qid],
        },
        headers=teacher,
    )
    sid = created.json()["id"]
    next_url, reveal_url = (
        f"/api/v1/session/{sid}/next",
        f"/api/v1/session/{sid}/reveal",
    )

    assert client.post(next_url, headers=teacher).status_code == 409  # in the lobby
    client.post(f"/api/v1/session/{sid}/start", headers=teacher)
    assert client.post(next_url, headers=teacher).status_code == 409  # not revealed
    client.post(reveal_url, headers=teacher)
    assert client.post(next_url, headers=teacher).json()["current_round_index"] == 1
    assert client.post(next_url, headers=teacher).status_code == 409  # the double tap
    assert client.get(f"/api/v1/session/{sid}").json()["current_round_index"] == 1

    client.post(reveal_url, headers=teacher)
    assert client.post(next_url, headers=teacher).json()["status"] == "completed"
    assert client.post(next_url, headers=teacher).status_code == 409  # after the end


def test_a_round_opened_by_a_concurrent_request_is_409_not_500(staff_db, client):
    _, conn = staff_db
    teacher = auth_headers(client, "teacher1")
    qid = _seed_question(conn)
    created = client.post(
        "/api/v1/session",
        json={"title": "Carrera", "topic": "arithmetic", "question_ids": [qid, qid]},
        headers=teacher,
    )
    sid = created.json()["id"]

    def _open(index: int) -> None:  # what the request that won the race left behind
        conn.execute(
            "UPDATE quiz_session_rounds SET status = 'open' WHERE id = ?",
            (f"{sid}_r{index}",),
        )
        conn.commit()

    _open(0)
    assert (
        client.post(f"/api/v1/session/{sid}/start", headers=teacher).status_code == 409
    )
    conn.execute("UPDATE quiz_session_rounds SET status = 'pending'")
    conn.commit()
    client.post(f"/api/v1/session/{sid}/start", headers=teacher)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher)
    _open(1)
    assert (
        client.post(f"/api/v1/session/{sid}/next", headers=teacher).status_code == 409
    )


def test_missing_active_round_returns_404(staff_db, client):
    _, conn = staff_db
    qid = _seed_question(conn)
    teacher_headers = auth_headers(client, "teacher1")
    s1_headers = auth_headers(client, "student1")

    create_resp = client.post(
        "/api/v1/session",
        json={"title": "No Round Test", "topic": "arithmetic", "question_ids": [qid]},
        headers=teacher_headers,
    )
    session_id = create_resp.json()["id"]

    # Tamper with session current_round_index to simulate corrupted/missing round
    conn.execute(
        "UPDATE quiz_sessions SET current_round_index = 999 WHERE id = ?",
        (session_id,),
    )
    conn.commit()

    assert (
        client.post(
            f"/api/v1/session/{session_id}/close", headers=teacher_headers
        ).status_code
        == 404
    )
    vote_resp = client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "A"},
        headers=s1_headers,
    )
    assert vote_resp.status_code == 404


def test_vote_invalid_option_error(staff_db, client, monkeypatch):
    from modes.quiz.session.engine import QuizSessionEngine
    from modes.quiz.session.exceptions import InvalidOptionError

    _, conn = staff_db
    qid = _seed_question(conn)
    teacher_headers = auth_headers(client, "teacher1")
    s1_headers = auth_headers(client, "student1")

    create_resp = client.post(
        "/api/v1/session",
        json={
            "title": "Invalid Option Test",
            "topic": "arithmetic",
            "question_ids": [qid],
        },
        headers=teacher_headers,
    )
    session_id = create_resp.json()["id"]
    client.post(f"/api/v1/session/{session_id}/start", headers=teacher_headers)

    def mock_cast_vote(*args, **kwargs):
        raise InvalidOptionError("Invalid option choice.")

    monkeypatch.setattr(QuizSessionEngine, "cast_vote", mock_cast_vote)

    vote_resp = client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "A"},
        headers=s1_headers,
    )
    assert vote_resp.status_code == 400
