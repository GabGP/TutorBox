"""Tests for /quiz/questions CRUD endpoints."""

from fastapi.testclient import TestClient

from db.quiz import create_question
from quiz.contracts.models import QuizQuestion
from tests.conftest import auth_headers

SAMPLE_QUESTION = QuizQuestion(
    id="q_crud_sample_01",
    topic="arithmetic",
    subconcept="addition_subtraction",
    question_text="¿Cuánto es 20 + 30?",
    options={"A": "50", "B": "40", "C": "60", "D": "55"},
    correct_option="A",
    distractors={
        "B": {
            "misconception": "subtraction_error",
            "explanation": "Restaste 10 en vez de sumar.",
        },
        "C": {
            "misconception": "forgot_carry",
            "explanation": "Sumaste 10 de más.",
        },
        "D": {
            "misconception": "table_lookup_error",
            "explanation": "Error de cálculo.",
        },
    },
)


def test_list_questions_rbac(staff_db, client: TestClient):
    """GET /quiz/questions enforces RBAC."""
    assert client.get("/quiz/questions").status_code == 401
    student_headers = auth_headers(client, "student1", "1234")
    assert client.get("/quiz/questions", headers=student_headers).status_code == 403

    teacher_headers = auth_headers(client, "teacher1", "1234")
    res = client.get("/quiz/questions", headers=teacher_headers)
    assert res.status_code == 200
    assert "questions" in res.json()
    assert "total" in res.json()


def test_list_questions_filtering_and_pagination(staff_db, client: TestClient):
    """GET /quiz/questions supports filtering and pagination."""
    _, conn = staff_db
    create_question(conn, question=SAMPLE_QUESTION, source="seed", sympy_verified=True)
    conn.commit()

    teacher_headers = auth_headers(client, "teacher1", "1234")
    res = client.get(
        "/quiz/questions?topic=arithmetic&limit=10&offset=0",
        headers=teacher_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert any(q["id"] == "q_crud_sample_01" for q in data["questions"])

    res_empty = client.get(
        "/quiz/questions?topic=nonexistent",
        headers=teacher_headers,
    )
    assert res_empty.status_code == 200
    assert res_empty.json()["total"] == 0
    assert res_empty.json()["questions"] == []


def test_get_question_by_id(staff_db, client: TestClient):
    """GET /quiz/questions/{id} returns single question or 404."""
    _, conn = staff_db
    create_question(conn, question=SAMPLE_QUESTION, source="seed", sympy_verified=True)
    conn.commit()

    teacher_headers = auth_headers(client, "teacher1", "1234")
    res_found = client.get(
        "/quiz/questions/q_crud_sample_01",
        headers=teacher_headers,
    )
    assert res_found.status_code == 200
    assert res_found.json()["id"] == "q_crud_sample_01"

    res_not_found = client.get(
        "/quiz/questions/nonexistent_id",
        headers=teacher_headers,
    )
    assert res_not_found.status_code == 404


def test_create_question_success(staff_db, client: TestClient):
    """POST /quiz/questions allows teacher to create a mathematically verified question."""
    _, conn = staff_db
    teacher_headers = auth_headers(client, "teacher1", "1234")

    payload = {
        "id": "q_teacher_01",
        "topic": "pre_algebra",
        "subconcept": "one_step_equations",
        "question_text": "¿Cuál es el valor de x en x + 5 = 12?",
        "options": {"A": "7", "B": "17", "C": "6", "D": "8"},
        "correct_option": "A",
        "distractors": {
            "B": {
                "misconception": "sign_flip_error",
                "explanation": "Sumaste 5 a 12 en vez de restar.",
            },
            "C": {
                "misconception": "table_lookup_error",
                "explanation": "Error menor al restar 5.",
            },
            "D": {
                "misconception": "wrong_inverse_operation",
                "explanation": "Error de cálculo.",
            },
        },
    }

    res = client.post("/quiz/questions", headers=teacher_headers, json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["id"] == "q_teacher_01"
    assert data["source"] == "teacher"
    assert data["sympy_verified"] is True
    assert data["schema_version"] == "1.0.0"

    audit_cursor = conn.execute(
        "SELECT * FROM audit_logs WHERE action = 'quiz_question_created'"
    )
    assert audit_cursor.fetchone() is not None

    # Test duplicate ID returns 409 Conflict
    res_duplicate = client.post(
        "/quiz/questions", headers=teacher_headers, json=payload
    )
    assert res_duplicate.status_code == 409
    assert "already exists" in res_duplicate.json()["detail"]


def test_create_question_invalid_topic_or_math(staff_db, client: TestClient):
    """POST /quiz/questions rejects invalid taxonomy or math errors with 422."""
    teacher_headers = auth_headers(client, "teacher1", "1234")

    bad_math_payload = {
        "id": "q_bad_math_01",
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
    res_math = client.post(
        "/quiz/questions", headers=teacher_headers, json=bad_math_payload
    )
    assert res_math.status_code == 422

    bad_topic_payload = dict(bad_math_payload)
    bad_topic_payload["topic"] = "invalid_topic"
    res_topic = client.post(
        "/quiz/questions", headers=teacher_headers, json=bad_topic_payload
    )
    assert res_topic.status_code == 422

    bad_subconcept_payload = dict(bad_math_payload)
    bad_subconcept_payload["subconcept"] = "invalid_subconcept"
    res_sub = client.post(
        "/quiz/questions", headers=teacher_headers, json=bad_subconcept_payload
    )
    assert res_sub.status_code == 422


def test_delete_question(staff_db, client: TestClient):
    """DELETE /quiz/questions/{id} soft deletes question and records audit."""
    _, conn = staff_db
    create_question(conn, question=SAMPLE_QUESTION, source="seed", sympy_verified=True)
    conn.commit()

    teacher_headers = auth_headers(client, "teacher1", "1234")
    res_del = client.delete(
        "/quiz/questions/q_crud_sample_01",
        headers=teacher_headers,
    )
    assert res_del.status_code == 200
    assert res_del.json()["detail"] == "Question deleted."

    res_del_again = client.delete(
        "/quiz/questions/q_crud_sample_01",
        headers=teacher_headers,
    )
    assert res_del_again.status_code == 404

    audit_cursor = conn.execute(
        "SELECT * FROM audit_logs WHERE action = 'quiz_question_deleted'"
    )
    assert audit_cursor.fetchone() is not None


def test_create_question_retrieval_failure_returns_500(
    staff_db, client: TestClient, monkeypatch
):
    """POST /quiz/questions returns 500 if question retrieval fails after creation."""
    from api.quiz import questions_write

    teacher_headers = auth_headers(client, "teacher1", "1234")
    monkeypatch.setattr(
        questions_write, "get_question_by_id", lambda *args, **kwargs: None
    )

    payload = {
        "id": "q_teacher_fail_500",
        "topic": "arithmetic",
        "subconcept": "addition_subtraction",
        "question_text": "¿Cuánto es 10 + 10?",
        "options": {"A": "20", "B": "19", "C": "21", "D": "30"},
        "correct_option": "A",
        "distractors": {
            "B": {"misconception": "sign_error", "explanation": "Explicación."},
            "C": {"misconception": "sign_error", "explanation": "Explicación."},
            "D": {"misconception": "sign_error", "explanation": "Explicación."},
        },
    }
    res = client.post("/quiz/questions", headers=teacher_headers, json=payload)
    assert res.status_code == 500
    assert "Failed to retrieve created question" in res.json()["detail"]
