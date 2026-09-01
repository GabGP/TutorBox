"""Tests for GET /quiz/schema contract endpoint."""

from fastapi.testclient import TestClient


def test_get_quiz_schema_success(client: TestClient):
    """GET /quiz/schema returns the canonical versioned JSON schema Draft 2020-12."""
    response = client.get("/quiz/schema")
    assert response.status_code == 200

    schema_payload = response.json()
    assert isinstance(schema_payload, dict)
    assert schema_payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert (
        schema_payload["$id"]
        == "https://tutorbox.local/schemas/v1/quiz_question.schema.json"
    )
    assert schema_payload["version"] == "1.0.0"
    assert schema_payload["title"] == "QuizQuestion"
    assert (
        schema_payload["description"]
        == "Canonical versioned contract schema for TutorBox diagnostic multiple-choice quiz questions."
    )

    properties = schema_payload["properties"]
    assert "id" in properties
    assert "topic" in properties
    assert "subconcept" in properties
    assert "question_text" in properties
    assert "options" in properties
    assert "correct_option" in properties
    assert "distractors" in properties
    assert "schema_version" in properties

    assert "$defs" in schema_payload
    assert "DistractorDetail" in schema_payload["$defs"]
