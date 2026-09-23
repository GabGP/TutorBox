"""Tests for PUT /api/v1/quiz/questions/{id}."""

from fastapi.testclient import TestClient

from core.db.question_repository import create_question
from modes.quiz.contracts.models import DistractorDetail, QuizQuestion
from tests.conftest import auth_headers

SAMPLE_QUESTION = QuizQuestion(
    id="q_crud_sample_01",
    topic="arithmetic",
    subconcept="addition_subtraction",
    question_text="¿Cuánto es 20 + 30?",
    options={"A": "50", "B": "40", "C": "60", "D": "55"},
    correct_option="A",
    distractors={
        "B": DistractorDetail(
            misconception="subtraction_error",
            explanation="Restaste 10 en vez de sumar.",
        ),
        "C": DistractorDetail(
            misconception="forgot_carry",
            explanation="Sumaste 10 de más.",
        ),
        "D": DistractorDetail(
            misconception="table_lookup_error",
            explanation="Error de cálculo.",
        ),
    },
)

VALID_EDIT_PAYLOAD = {
    "topic": "arithmetic",
    "subconcept": "addition_subtraction",
    "question_text": "¿Cuánto es 25 + 30?",
    "options": {"A": "55", "B": "45", "C": "65", "D": "50"},
    "correct_option": "A",
    "distractors": {
        "B": {"misconception": "sign_error", "explanation": "Restaste 10."},
        "C": {"misconception": "sign_error", "explanation": "Sumaste 10 de más."},
        "D": {"misconception": "sign_error", "explanation": "Error de cálculo."},
    },
}


def test_update_question_success(staff_db, client: TestClient):
    """PUT /api/v1/quiz/questions/{id} edits a question after re-validation."""
    _, conn = staff_db
    create_question(conn, question=SAMPLE_QUESTION, source="seed", sympy_verified=True)
    conn.commit()

    teacher_headers = auth_headers(client, "teacher1", "1234")
    res = client.put(
        "/api/v1/quiz/questions/q_crud_sample_01",
        headers=teacher_headers,
        json=VALID_EDIT_PAYLOAD,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "q_crud_sample_01"
    assert data["question_text"] == "¿Cuánto es 25 + 30?"
    assert data["source"] == "teacher"
    assert data["sympy_verified"] is True

    audit_cursor = conn.execute(
        "SELECT * FROM audit_logs WHERE action = 'quiz_question_updated'"
    )
    assert audit_cursor.fetchone() is not None


def test_update_question_not_found_or_deleted(staff_db, client: TestClient):
    """PUT returns 404 for missing or soft-deleted questions."""
    _, conn = staff_db
    create_question(conn, question=SAMPLE_QUESTION, source="seed", sympy_verified=True)
    conn.commit()

    teacher_headers = auth_headers(client, "teacher1", "1234")
    res_missing = client.put(
        "/api/v1/quiz/questions/does_not_exist",
        headers=teacher_headers,
        json=VALID_EDIT_PAYLOAD,
    )
    assert res_missing.status_code == 404

    client.delete("/api/v1/quiz/questions/q_crud_sample_01", headers=teacher_headers)
    res_deleted = client.put(
        "/api/v1/quiz/questions/q_crud_sample_01",
        headers=teacher_headers,
        json=VALID_EDIT_PAYLOAD,
    )
    assert res_deleted.status_code == 404


def test_update_question_rejects_bad_math_and_roles(staff_db, client: TestClient):
    """PUT enforces math validation and teacher/admin RBAC."""
    _, conn = staff_db
    create_question(conn, question=SAMPLE_QUESTION, source="seed", sympy_verified=True)
    conn.commit()

    teacher_headers = auth_headers(client, "teacher1", "1234")
    bad_payload = {
        "topic": "arithmetic",
        "subconcept": "addition_subtraction",
        "question_text": "¿Cuánto es 10 + 10?",
        "options": {"A": "99", "B": "20", "C": "30", "D": "40"},
        "correct_option": "A",
        "distractors": {
            "B": {"misconception": "sign_error", "explanation": "Explicación."},
            "C": {"misconception": "sign_error", "explanation": "Explicación."},
            "D": {"misconception": "sign_error", "explanation": "Explicación."},
        },
    }
    res_math = client.put(
        "/api/v1/quiz/questions/q_crud_sample_01",
        headers=teacher_headers,
        json=bad_payload,
    )
    assert res_math.status_code == 422

    student_headers = auth_headers(client, "student1", "1234")
    res_student = client.put(
        "/api/v1/quiz/questions/q_crud_sample_01",
        headers=student_headers,
        json=bad_payload,
    )
    assert res_student.status_code == 403


def test_update_question_rejects_invalid_taxonomy(staff_db, client: TestClient):
    """PUT rejects invalid topic and subconcept combinations with 422."""
    _, conn = staff_db
    create_question(conn, question=SAMPLE_QUESTION, source="seed", sympy_verified=True)
    conn.commit()

    teacher_headers = auth_headers(client, "teacher1", "1234")

    # Invalid topic
    bad_topic_payload = {**VALID_EDIT_PAYLOAD, "topic": "nonexistent_topic"}
    res_topic = client.put(
        "/api/v1/quiz/questions/q_crud_sample_01",
        headers=teacher_headers,
        json=bad_topic_payload,
    )
    assert res_topic.status_code == 422
    assert "Invalid topic" in res_topic.json()["detail"]

    # Invalid subconcept
    bad_sub_payload = {**VALID_EDIT_PAYLOAD, "subconcept": "invalid_sub"}
    res_sub = client.put(
        "/api/v1/quiz/questions/q_crud_sample_01",
        headers=teacher_headers,
        json=bad_sub_payload,
    )
    assert res_sub.status_code == 422
    assert "Invalid subconcept" in res_sub.json()["detail"]


def test_update_question_retrieval_failure_returns_500(
    staff_db, client: TestClient, monkeypatch
):
    """PUT returns 500 if database update succeeds but retrieval fails."""
    _, conn = staff_db
    create_question(conn, question=SAMPLE_QUESTION, source="seed", sympy_verified=True)
    conn.commit()

    import api.quiz.questions_update as qu_mod

    monkeypatch.setattr(qu_mod, "get_question_by_id", lambda *args, **kwargs: None)
    teacher_headers = auth_headers(client, "teacher1", "1234")
    res = client.put(
        "/api/v1/quiz/questions/q_crud_sample_01",
        headers=teacher_headers,
        json=VALID_EDIT_PAYLOAD,
    )
    assert res.status_code == 500
