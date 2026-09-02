"""Unit tests for the centralized API router topology."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import api_v1_router, root_router


def test_api_v1_router_prefixes():
    """Verifies that api_v1_router contains all expected sub-domain route paths."""
    dummy_app = FastAPI()
    dummy_app.include_router(api_v1_router)

    openapi = dummy_app.openapi()
    paths = openapi.get("paths", {})
    assert any(path.startswith("/api/v1/auth") for path in paths)
    assert any(path.startswith("/api/v1/users") for path in paths)
    assert any(path.startswith("/api/v1/staff") for path in paths)
    assert any(path.startswith("/api/v1/quiz") for path in paths)


def test_root_router_mounts_health_and_v1():
    """Verifies that root_router mounts the health endpoint and api_v1_router tree."""
    dummy_app = FastAPI()
    dummy_app.include_router(root_router)
    client = TestClient(dummy_app)

    response = client.get("/health")
    assert response.status_code == 200

    openapi = dummy_app.openapi()
    paths = openapi.get("paths", {})
    assert "/health" in paths
    assert any(path.startswith("/api/v1/auth") for path in paths)
    assert any(path.startswith("/api/v1/users") for path in paths)
    assert any(path.startswith("/api/v1/staff") for path in paths)
    assert any(path.startswith("/api/v1/quiz") for path in paths)
