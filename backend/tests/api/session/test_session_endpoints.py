"""Integration tests for the quiz session REST API endpoints."""

from core.db.question_repository import create_question
from quiz.contracts.models import DistractorDetail, QuizQuestionCreate
from tests.conftest import auth_headers


def _seed_quiz_questions(conn) -> list[str]:
    q1 = create_question(
        conn,
        QuizQuestionCreate(
            topic="arithmetic",
            subconcept="addition",
            question_text="2 + 3?",
            options={"A": "5", "B": "6", "C": "4", "D": "1"},
            correct_option="A",
            distractors={
                "B": DistractorDetail(
                    misconception="plus_one", explanation="Sumaste 1 de mas."
                ),
                "C": DistractorDetail(
                    misconception="minus_one", explanation="Sumaste 1 de menos."
                ),
                "D": DistractorDetail(
                    misconception="subtracted", explanation="Restaste."
                ),
            },
        ),
    )
    q2 = create_question(
        conn,
        QuizQuestionCreate(
            topic="arithmetic",
            subconcept="multiplication",
            question_text="3 * 4?",
            options={"A": "12", "B": "7", "C": "14", "D": "10"},
            correct_option="A",
            distractors={
                "B": DistractorDetail(
                    misconception="added_numbers",
                    explanation="Sumaste en vez de multiplicar.",
                ),
                "C": DistractorDetail(
                    misconception="table_error", explanation="Error en tabla."
                ),
                "D": DistractorDetail(
                    misconception="off_by_two", explanation="Desfase de 2."
                ),
            },
        ),
    )
    conn.commit()
    return [q1, q2]


def test_create_session_permissions(staff_db, client):
    _, conn = staff_db
    q_ids = _seed_quiz_questions(conn)
    student_headers = auth_headers(client, "student1")
    teacher_headers = auth_headers(client, "teacher1")

    payload = {
        "title": "Math Quiz",
        "topic": "arithmetic",
        "question_ids": q_ids,
        "duration_seconds": 30,
    }

    # Unauthenticated
    assert client.post("/api/v1/session", json=payload).status_code == 401
    # Student forbidden
    assert (
        client.post(
            "/api/v1/session", json=payload, headers=student_headers
        ).status_code
        == 403
    )
    # Teacher succeeds
    resp = client.post("/api/v1/session", json=payload, headers=teacher_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "lobby"
    assert data["question_count"] == 2


def test_get_session_state_and_404(staff_db, client):
    _, conn = staff_db
    q_ids = _seed_quiz_questions(conn)
    teacher_headers = auth_headers(client, "teacher1")

    create_resp = client.post(
        "/api/v1/session",
        json={"title": "State Test", "topic": "arithmetic", "question_ids": q_ids},
        headers=teacher_headers,
    )
    session_id = create_resp.json()["id"]

    # Public get session
    get_resp = client.get(f"/api/v1/session/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "State Test"

    # Nonexistent session
    assert client.get("/api/v1/session/nonexistent_id").status_code == 404


def test_start_session_lifecycle(staff_db, client):
    _, conn = staff_db
    q_ids = _seed_quiz_questions(conn)
    teacher_headers = auth_headers(client, "teacher1")
    student_headers = auth_headers(client, "student1")

    create_resp = client.post(
        "/api/v1/session",
        json={"title": "Start Test", "topic": "arithmetic", "question_ids": q_ids},
        headers=teacher_headers,
    )
    session_id = create_resp.json()["id"]

    # Student forbidden to start
    assert (
        client.post(
            f"/api/v1/session/{session_id}/start", headers=student_headers
        ).status_code
        == 403
    )

    # Teacher starts session
    start_resp = client.post(
        f"/api/v1/session/{session_id}/start", headers=teacher_headers
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "active"
    assert start_resp.json()["current_round"]["status"] == "open"

    # Starting again conflicts (409)
    assert (
        client.post(
            f"/api/v1/session/{session_id}/start", headers=teacher_headers
        ).status_code
        == 409
    )


def test_vote_first_press_lock_and_validation(staff_db, client):
    _, conn = staff_db
    q_ids = _seed_quiz_questions(conn)
    teacher_headers = auth_headers(client, "teacher1")
    s1_headers = auth_headers(client, "student1")
    s2_headers = auth_headers(client, "student2")

    create_resp = client.post(
        "/api/v1/session",
        json={"title": "Vote Test", "topic": "arithmetic", "question_ids": q_ids},
        headers=teacher_headers,
    )
    session_id = create_resp.json()["id"]
    client.post(f"/api/v1/session/{session_id}/start", headers=teacher_headers)

    # First vote from student 1 succeeds
    v1_resp = client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "A"},
        headers=s1_headers,
    )
    assert v1_resp.status_code == 200
    assert v1_resp.json()["selected_option"] == "A"

    # Duplicate vote from student 1 returns 409 Conflict
    dup_resp = client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "B"},
        headers=s1_headers,
    )
    assert dup_resp.status_code == 409

    # Second student votes distractor B
    v2_resp = client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "B"},
        headers=s2_headers,
    )
    assert v2_resp.status_code == 200

    # Invalid option returns 400
    assert (
        client.post(
            f"/api/v1/session/{session_id}/vote",
            json={"selected_option": "Z"},
            headers=auth_headers(client, "admin1"),
        ).status_code
        == 422
    )


def test_close_reveal_next_and_report_flow(staff_db, client):
    _, conn = staff_db
    q_ids = _seed_quiz_questions(conn)
    teacher_headers = auth_headers(client, "teacher1")
    s1_headers = auth_headers(client, "student1")

    create_resp = client.post(
        "/api/v1/session",
        json={"title": "Flow Test", "topic": "arithmetic", "question_ids": q_ids},
        headers=teacher_headers,
    )
    session_id = create_resp.json()["id"]
    client.post(f"/api/v1/session/{session_id}/start", headers=teacher_headers)
    client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": "A"},
        headers=s1_headers,
    )

    # Close round
    close_resp = client.post(
        f"/api/v1/session/{session_id}/close", headers=teacher_headers
    )
    assert close_resp.status_code == 200

    # Reveal round
    reveal_resp = client.post(
        f"/api/v1/session/{session_id}/reveal", headers=teacher_headers
    )
    assert reveal_resp.status_code == 200
    reveal_data = reveal_resp.json()
    assert reveal_data["tally"]["total_votes"] == 1
    assert reveal_data["decision"]["should_speak"] is False

    # Next round
    next_resp = client.post(
        f"/api/v1/session/{session_id}/next", headers=teacher_headers
    )
    assert next_resp.status_code == 200
    assert next_resp.json()["current_round_index"] == 1

    # Complete session
    final_next = client.post(
        f"/api/v1/session/{session_id}/next", headers=teacher_headers
    )
    assert final_next.status_code == 200
    assert final_next.json()["status"] == "completed"

    # Report
    report_resp = client.get(
        f"/api/v1/session/{session_id}/report", headers=teacher_headers
    )
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report["total_votes_cast"] == 1
    assert report["average_accuracy_percentage"] == 100.0
