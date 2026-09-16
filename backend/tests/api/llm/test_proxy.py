"""Integration tests for the /api/v1/llm lifecycle proxy endpoints."""

import urllib.error
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def test_llm_load_success(client: TestClient, admin_headers: dict[str, str]) -> None:
    """Verifies POST /api/v1/llm/load succeeds and proxies payload to llama-server."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"status": "ok", "detail": "Model loaded"}'
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = client.post(
            "/api/v1/llm/load",
            json={"model": "qwen-0.6b"},
            headers=admin_headers,
        )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["detail"] == "Model loaded"


def test_llm_load_server_unreachable(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    """Verifies POST /api/v1/llm/load returns 503 when llama-server is offline."""
    with patch("urllib.request.urlopen", side_effect=OSError("Connection refused")):
        res = client.post(
            "/api/v1/llm/load",
            json={"model": "test"},
            headers=admin_headers,
        )
    assert res.status_code == 503
    assert "unreachable" in res.json()["detail"].lower()


def test_llm_load_forbidden_for_teacher(
    client: TestClient, teacher_headers: dict[str, str]
) -> None:
    """Verifies POST /api/v1/llm/load returns 403 for non-admin users."""
    res = client.post(
        "/api/v1/llm/load",
        json={"model": "test"},
        headers=teacher_headers,
    )
    assert res.status_code == 403


def test_llm_unload_success(client: TestClient, admin_headers: dict[str, str]) -> None:
    """Verifies POST /api/v1/llm/unload succeeds."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"status": "ok", "detail": "Model unloaded"}'
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = client.post("/api/v1/llm/unload", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_llm_status_success(client: TestClient, admin_headers: dict[str, str]) -> None:
    """Verifies GET /api/v1/llm/status returns models list from llama-server."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"models": [{"name": "qwen", "size": 1024}]}'
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = client.get("/api/v1/llm/status", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert len(data["models"]) == 1
    assert data["models"][0]["name"] == "qwen"


def test_llm_proxy_http_error(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    """Verifies HTTP error from llama-server is forwarded with same status code."""
    error = urllib.error.HTTPError(
        url="http://127.0.0.1:8080/models/load",
        code=500,
        msg="Internal Error",
        hdrs=MagicMock(),
        fp=MagicMock(read=lambda: b"CUDA out of memory"),
    )
    with patch("urllib.request.urlopen", side_effect=error):
        res = client.post("/api/v1/llm/load", json={}, headers=admin_headers)
    assert res.status_code == 500
    assert "CUDA out of memory" in res.json()["detail"]
