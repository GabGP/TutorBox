"""Tests for POST /api/v1/quiz/validate endpoint."""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def test_validate_question_rbac(staff_db, client: TestClient):
    """POST /api/v1/quiz/validate enforces teacher/admin RBAC."""
    payload = {
        "question": {
            "id": "q_test_rbac",
            "topic": "arithmetic",
            "subconcept": "addition_subtraction",
            "question_text": "¿Cuánto es 10 + 5?",
            "options": {"A": "15", "B": "14", "C": "12", "D": "13"},
            "correct_option": "A",
            "distractors": {
                "B": {"misconception": "table_lookup_error", "explanation": "Error."},
                "C": {"misconception": "subtraction_error", "explanation": "Error."},
                "D": {"misconception": "rounding_error", "explanation": "Error."},
            },
        }
    }
    # Unauthenticated request returns 401
    unauth_res = client.post("/api/v1/quiz/validate", json=payload)
    assert unauth_res.status_code == 401

    # Student role returns 403
    student_headers = auth_headers(client, "student1", "1234")
    student_res = client.post(
        "/api/v1/quiz/validate", json=payload, headers=student_headers
    )
    assert student_res.status_code == 403

    # Teacher role succeeds (200)
    teacher_headers = auth_headers(client, "teacher1", "1234")
    teacher_res = client.post(
        "/api/v1/quiz/validate", json=payload, headers=teacher_headers
    )
    assert teacher_res.status_code == 200

    # Admin role succeeds (200)
    admin_headers = auth_headers(client, "admin1", "1234")
    admin_res = client.post(
        "/api/v1/quiz/validate", json=payload, headers=admin_headers
    )
    assert admin_res.status_code == 200


def test_validate_question_success(client: TestClient, teacher_headers: dict[str, str]):
    """POST /api/v1/quiz/validate succeeds for a mathematically valid diagnostic question."""
    valid_payload = {
        "question": {
            "id": "q_test_val_01",
            "topic": "arithmetic",
            "subconcept": "addition_subtraction",
            "question_text": "¿Cuánto es 15 + 27?",
            "options": {"A": "42", "B": "32", "C": "41", "D": "52"},
            "correct_option": "A",
            "distractors": {
                "B": {
                    "misconception": "forgot_carry",
                    "explanation": "Sumaste 5+7 pero no llevaste el 1.",
                },
                "C": {
                    "misconception": "table_lookup_error",
                    "explanation": "Cometiste un error menor al sumar 5+7.",
                },
                "D": {
                    "misconception": "sign_error",
                    "explanation": "Sumaste una decena de más.",
                },
            },
        }
    }
    response = client.post(
        "/api/v1/quiz/validate", json=valid_payload, headers=teacher_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["errors"] == []


def test_validate_question_math_error(
    client: TestClient, teacher_headers: dict[str, str]
):
    """POST /api/v1/quiz/validate detects incorrect math in correct_option."""
    invalid_math_payload = {
        "question": {
            "id": "q_test_val_02",
            "topic": "arithmetic",
            "subconcept": "addition_subtraction",
            "question_text": "¿Cuánto es 15 + 27?",
            "options": {"A": "99", "B": "32", "C": "41", "D": "52"},
            "correct_option": "A",
            "distractors": {
                "B": {
                    "misconception": "forgot_carry",
                    "explanation": "Sumaste 5+7 pero no llevaste el 1.",
                },
                "C": {
                    "misconception": "table_lookup_error",
                    "explanation": "Cometiste un error menor.",
                },
                "D": {
                    "misconception": "sign_error",
                    "explanation": "Sumaste una decena de más.",
                },
            },
        }
    }
    response = client.post(
        "/api/v1/quiz/validate", json=invalid_math_payload, headers=teacher_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert len(data["errors"]) >= 1


def test_validate_question_distractor_collision(
    client: TestClient, teacher_headers: dict[str, str]
):
    """POST /api/v1/quiz/validate detects distractor evaluating to correct answer."""
    collision_payload = {
        "question": {
            "id": "q_test_val_03",
            "topic": "arithmetic",
            "subconcept": "addition_subtraction",
            "question_text": "¿Cuánto es 10 + 5?",
            "options": {"A": "15", "B": "15", "C": "12", "D": "13"},
            "correct_option": "A",
            "distractors": {
                "B": {
                    "misconception": "duplicate_value",
                    "explanation": "Esta opción es igual a la correcta.",
                },
                "C": {
                    "misconception": "subtraction_error",
                    "explanation": "Error de cálculo.",
                },
                "D": {
                    "misconception": "rounding_error",
                    "explanation": "Error de cálculo.",
                },
            },
        }
    }
    response = client.post(
        "/api/v1/quiz/validate", json=collision_payload, headers=teacher_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert any("Distractor 'B'" in err for err in data["errors"])


def test_validate_question_schema_failure(
    client: TestClient, teacher_headers: dict[str, str]
):
    """POST /api/v1/quiz/validate returns 422 if the JSON structure violates schema rules."""
    bad_schema_payload = {
        "question": {
            "id": "q_bad",
            "topic": "arithmetic",
            "subconcept": "addition_subtraction",
            "question_text": "¿Cuánto es 10 + 5?",
            "options": {"A": "15", "B": "12"},
            "correct_option": "A",
            "distractors": {},
        }
    }
    response = client.post(
        "/api/v1/quiz/validate", json=bad_schema_payload, headers=teacher_headers
    )
    assert response.status_code == 422


def test_validate_question_adversarial_rce_payload(
    client: TestClient, teacher_headers: dict[str, str]
):
    """Adversarial test: python attribute traversal in options is safely rejected."""
    exploit_payload = {
        "question": {
            "id": "q_exploit",
            "topic": "arithmetic",
            "subconcept": "addition_subtraction",
            "question_text": "¿Cuánto es 10 + 5?",
            "options": {
                "A": "15",
                "B": "().__class__.__mro__[1].__name__",
                "C": "12",
                "D": "13",
            },
            "correct_option": "A",
            "distractors": {
                "B": {
                    "misconception": "table_lookup_error",
                    "explanation": "Error de cálculo.",
                },
                "C": {
                    "misconception": "subtraction_error",
                    "explanation": "Error de cálculo.",
                },
                "D": {
                    "misconception": "rounding_error",
                    "explanation": "Error de cálculo.",
                },
            },
        }
    }
    # Unauthenticated request blocked by RBAC
    assert client.post("/api/v1/quiz/validate", json=exploit_payload).status_code == 401

    # Authenticated teacher request handled safely without code execution
    response = client.post(
        "/api/v1/quiz/validate", json=exploit_payload, headers=teacher_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
