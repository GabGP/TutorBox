"""Unit and integration tests for FastAPI main application lifecycle, router mounts, and env loading."""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app, lifespan, load_env_file


def test_load_env_file_parses_unloaded_keys(monkeypatch):
    """Verifies that load_env_file reads keys into os.environ if not already present."""
    fake_env_content = (
        "TEST_MAIN_CUSTOM_KEY=custom_value\n# Comment\ninvalid_no_equal\n"
    )
    monkeypatch.delenv("TEST_MAIN_CUSTOM_KEY", raising=False)
    with (
        patch("main.Path.is_file", return_value=True),
        patch("main.Path.read_text", return_value=fake_env_content),
    ):
        load_env_file()
        assert os.environ.get("TEST_MAIN_CUSTOM_KEY") == "custom_value"


def test_load_env_file_graceful_when_no_file():
    """Verifies that load_env_file handles missing .env files without error."""
    with patch("main.Path.is_file", return_value=False):
        load_env_file()


@pytest.mark.anyio
async def test_app_lifespan_executes_migrations_and_seeding():
    """Verifies that the application lifespan context executes migrations and seed bank."""
    with (
        patch("main.apply_migrations") as mock_apply,
        patch("main.seed_question_bank", return_value=5) as mock_seed,
    ):
        async with lifespan(app):
            mock_apply.assert_called_once()
            mock_seed.assert_called_once()


def test_app_routes_mounted():
    """Verifies that all required sub-routers are registered on the main FastAPI app."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200

    openapi = app.openapi()
    paths = openapi.get("paths", {})
    assert "/health" in paths
    assert any(path.startswith("/api/v1/auth") for path in paths)
    assert any(path.startswith("/api/v1/users") for path in paths)
    assert any(path.startswith("/api/v1/staff") for path in paths)
    assert any(path.startswith("/api/v1/quiz") for path in paths)
