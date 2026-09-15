"""Unit and integration tests for FastAPI main application lifecycle, router mounts, and env loading."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import (
    CLIENT_MOUNTS,
    DEFAULT_CLIENT_DIR,
    app,
    lifespan,
    load_env_file,
    resolve_client_dir,
    validate_client_dir,
)


def test_load_env_file_parses_unloaded_keys(monkeypatch):
    """Verifies that load_env_file reads keys into os.environ if not already present."""
    fake_env_content = (
        "TEST_MAIN_CUSTOM_KEY=custom_value\n# Comment\ninvalid_no_equal\n"
    )
    monkeypatch.delenv("TEST_MAIN_CUSTOM_KEY", raising=False)
    with (
        patch("core.config.env_loader.Path.is_file", return_value=True),
        patch("core.config.env_loader.Path.read_text", return_value=fake_env_content),
    ):
        load_env_file()
        assert os.environ.get("TEST_MAIN_CUSTOM_KEY") == "custom_value"


def test_load_env_file_graceful_when_no_file():
    """Verifies that load_env_file handles missing .env files without error."""
    with patch("core.config.env_loader.Path.is_file", return_value=False):
        load_env_file()


@pytest.mark.anyio
async def test_app_lifespan_executes_migrations_and_seeding():
    """Verifies that the application lifespan context executes migrations and seed bank."""
    with (
        patch("main.apply_migrations") as mock_apply,
        patch("main.seed_question_bank", return_value=5) as mock_seed,
        patch("main.seed_teacher", return_value=True) as mock_teacher,
    ):
        async with lifespan(app):
            mock_apply.assert_called_once()
            mock_seed.assert_called_once()
            mock_teacher.assert_called_once()


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


def test_resolve_client_dir_defaults_to_dist(monkeypatch):
    """Verifies resolve_client_dir returns React build output when env is unset."""
    monkeypatch.delenv("PWA_STATIC_DIR", raising=False)
    resolved = resolve_client_dir()
    assert resolved == DEFAULT_CLIENT_DIR
    assert resolved.name == "dist"


def test_resolve_client_dir_handles_empty_string(monkeypatch):
    """Verifies resolve_client_dir returns default when given empty or whitespace."""
    monkeypatch.delenv("PWA_STATIC_DIR", raising=False)
    assert resolve_client_dir("   ") == DEFAULT_CLIENT_DIR


def test_resolve_client_dir_explicit_pilas_override():
    """Verifies legacy pilas client stays selectable via explicit override."""
    resolved = resolve_client_dir("pwa/pilas")
    assert resolved.name == "pilas"
    assert resolved.parent.name == "pwa"


def test_validate_client_dir_rejects_missing_mounts(tmp_path):
    """Verifies fail-fast error when the client directory lacks mounts."""
    with pytest.raises(RuntimeError, match="Classroom web client directory missing"):
        validate_client_dir(tmp_path)


def test_validate_client_dir_accepts_complete_dir(tmp_path):
    """Verifies validation passes when all mounts are present."""
    for mount in CLIENT_MOUNTS:
        (tmp_path / mount).mkdir()
    assert validate_client_dir(tmp_path) == tmp_path


def test_resolve_client_dir_resolves_relative_and_absolute_paths():
    """Verifies resolve_client_dir handles both custom relative and absolute paths."""
    rel = resolve_client_dir("custom/static/dir")
    assert rel.name == "dir"
    assert rel.parent.name == "static"

    abs_path = Path.cwd().resolve()
    assert resolve_client_dir(str(abs_path)) == abs_path
