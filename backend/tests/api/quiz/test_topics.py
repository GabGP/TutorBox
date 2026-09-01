"""Tests for GET /api/v1/quiz/topics taxonomy endpoint."""

from fastapi.testclient import TestClient


def test_get_quiz_topics_structure(client: TestClient):
    """GET /api/v1/quiz/topics returns the curriculum taxonomy hierarchy."""
    response = client.get("/api/v1/quiz/topics")
    assert response.status_code == 200
    topics_list = response.json()
    assert isinstance(topics_list, list)
    assert len(topics_list) >= 4

    topic_names = [topic_item["name"] for topic_item in topics_list]
    assert "arithmetic" in topic_names
    assert "fractions" in topic_names
    assert "pre_algebra" in topic_names
    assert "decimals_percentages" in topic_names

    for topic_item in topics_list:
        assert "name" in topic_item
        assert "subconcepts" in topic_item
        assert len(topic_item["subconcepts"]) >= 1
        for subconcept_item in topic_item["subconcepts"]:
            assert "name" in subconcept_item
            assert "misconceptions" in subconcept_item
            assert isinstance(subconcept_item["misconceptions"], list)
            assert len(subconcept_item["misconceptions"]) >= 1
