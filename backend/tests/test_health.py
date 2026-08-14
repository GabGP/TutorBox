from fastapi.testclient import TestClient


def test_health_check_healthy(client: TestClient):
    """
    Test that /health returns 200 OK and healthy status when database is available.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "TutorBox Backend"
    assert data["database"] == "healthy"


def test_health_check_returns_json(client: TestClient):
    """
    Test that /health endpoint returns application/json content type.
    """
    response = client.get("/health")
    assert response.headers["content-type"].startswith("application/json")


def test_health_check_structure(client: TestClient):
    """
    Test that /health response contains all expected keys.
    """
    response = client.get("/health")
    data = response.json()
    assert set(data.keys()) == {"status", "service", "database"}
