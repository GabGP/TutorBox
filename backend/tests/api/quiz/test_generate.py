"""Tests for POST /quiz/generate endpoint."""

import json

from fastapi.testclient import TestClient
from llm import MockLLMClient

from api.quiz.dependencies import get_quiz_generator
from quiz.generation.generator import QuizQuestionGenerator
from src.main import app
from tests.conftest import auth_headers

VALID_LLM_OUTPUT = json.dumps(
    {
        "id": "q_gen_test_01",
        "topic": "arithmetic",
        "subconcept": "addition_subtraction",
        "question_text": "¿Cuánto es 12 + 15?",
        "options": {"A": "27", "B": "26", "C": "37", "D": "17"},
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "borrowing_error",
                "explanation": "Calculaste mal la suma de las unidades.",
            },
            "C": {
                "misconception": "alignment_error",
                "explanation": "Alineaste mal las decenas.",
            },
            "D": {
                "misconception": "added_instead_of_subtracted",
                "explanation": "Restaste en vez de sumar.",
            },
        },
    }
)


def test_generate_question_rbac_unauthenticated(client: TestClient):
    """POST /quiz/generate returns 401 Unauthorized for unauthenticated callers."""
    response = client.post(
        "/quiz/generate",
        json={"topic": "arithmetic", "subconcept": "addition_subtraction"},
    )
    assert response.status_code == 401


def test_generate_question_rbac_student_forbidden(staff_db, client: TestClient):
    """POST /quiz/generate returns 403 Forbidden for students."""
    headers = auth_headers(client, "student1", "1234")
    response = client.post(
        "/quiz/generate",
        headers=headers,
        json={"topic": "arithmetic", "subconcept": "addition_subtraction"},
    )
    assert response.status_code == 403


def test_generate_question_rbac_rotation_pending_forbidden(temp_db, client: TestClient):
    """POST /quiz/generate returns 403 Forbidden when PIN rotation is pending."""
    from security.auth import hash_pin

    _, conn = temp_db
    conn.execute(
        "INSERT INTO users (username, hashed_pin, role, must_change_pin) "
        "VALUES ('teacher_rot', ?, 'teacher', 1)",
        (hash_pin("1234"),),
    )
    conn.commit()

    login_res = client.post("/login", json={"username": "teacher_rot", "pin": "1234"})
    token = login_res.json()["session_id"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/quiz/generate",
        headers=headers,
        json={"topic": "arithmetic", "subconcept": "addition_subtraction"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "PIN change required."


def test_generate_question_success_no_save(staff_db, client: TestClient):
    """Teacher generates question without saving to bank."""
    mock_llm = MockLLMClient([VALID_LLM_OUTPUT])
    app.dependency_overrides[get_quiz_generator] = lambda: QuizQuestionGenerator(
        llm_client=mock_llm
    )

    try:
        headers = auth_headers(client, "teacher1", "1234")
        response = client.post(
            "/quiz/generate",
            headers=headers,
            json={
                "topic": "arithmetic",
                "subconcept": "addition_subtraction",
                "save_to_bank": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "arithmetic"
        assert data["correct_option"] in {"A", "B", "C", "D"}
        assert data["options"][data["correct_option"]] == "27"
        assert data["sympy_verified"] is True
    finally:
        app.dependency_overrides.pop(get_quiz_generator, None)


def test_generate_question_success_and_save_to_bank(staff_db, client: TestClient):
    """Teacher generates question and persists it to question bank with audit log."""
    _, conn = staff_db
    mock_llm = MockLLMClient([VALID_LLM_OUTPUT])
    app.dependency_overrides[get_quiz_generator] = lambda: QuizQuestionGenerator(
        llm_client=mock_llm
    )

    try:
        headers = auth_headers(client, "teacher1", "1234")
        response = client.post(
            "/quiz/generate",
            headers=headers,
            json={
                "topic": "arithmetic",
                "subconcept": "addition_subtraction",
                "save_to_bank": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        question_id = data["id"]
        assert data["source"] == "llm"
        assert data["sympy_verified"] is True

        cursor = conn.execute(
            "SELECT * FROM quiz_questions WHERE id = ?", (question_id,)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["topic"] == "arithmetic"

        audit_cursor = conn.execute(
            "SELECT * FROM audit_logs WHERE action = 'quiz_question_generated'"
        )
        audit_row = audit_cursor.fetchone()
        assert audit_row is not None
    finally:
        app.dependency_overrides.pop(get_quiz_generator, None)


def test_generate_question_invalid_topic_subconcept(staff_db, client: TestClient):
    """POST /quiz/generate validates topic and subconcept existence."""
    headers = auth_headers(client, "teacher1", "1234")

    bad_topic_res = client.post(
        "/quiz/generate",
        headers=headers,
        json={"topic": "nonexistent_topic"},
    )
    assert bad_topic_res.status_code == 422

    bad_sub_res = client.post(
        "/quiz/generate",
        headers=headers,
        json={"topic": "arithmetic", "subconcept": "nonexistent_subconcept"},
    )
    assert bad_sub_res.status_code == 422


def test_generate_question_llm_failure_returns_502(staff_db, client: TestClient):
    """POST /quiz/generate returns 502 when LLM outputs unrecoverable malformed text."""
    mock_llm = MockLLMClient(["invalid text"] * 5)
    app.dependency_overrides[get_quiz_generator] = lambda: QuizQuestionGenerator(
        llm_client=mock_llm
    )

    try:
        headers = auth_headers(client, "admin1", "1234")
        response = client.post(
            "/quiz/generate",
            headers=headers,
            json={"topic": "arithmetic", "subconcept": "addition_subtraction"},
        )
        assert response.status_code == 502
        assert "Failed to generate valid quiz question" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_quiz_generator, None)
