"""Tests for POST /quiz/validate endpoint."""

from fastapi.testclient import TestClient


def test_validate_question_success(client: TestClient):
    """POST /quiz/validate succeeds for a mathematically valid diagnostic question."""
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
    response = client.post("/quiz/validate", json=valid_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["errors"] == []


def test_validate_question_math_error(client: TestClient):
    """POST /quiz/validate detects incorrect math in correct_option."""
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
    response = client.post("/quiz/validate", json=invalid_math_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert len(data["errors"]) >= 1


def test_validate_question_distractor_collision(client: TestClient):
    """POST /quiz/validate detects distractor evaluating to correct answer."""
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
    response = client.post("/quiz/validate", json=collision_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert any("Distractor 'B'" in err for err in data["errors"])


def test_validate_question_schema_failure(client: TestClient):
    """POST /quiz/validate returns 422 if the JSON structure violates schema rules."""
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
    response = client.post("/quiz/validate", json=bad_schema_payload)
    assert response.status_code == 422
