"""Integration tests for the /api/v1/tts lifecycle endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from core.tts.exceptions import TTSUnavailableError


def test_tts_load_success(client: TestClient, teacher_headers: dict[str, str]) -> None:
    """Verifies POST /api/v1/tts/load returns 202 Accepted and preload metrics."""
    with (
        patch("core.tts.router.TTSRouter.preload", return_value=("piper", 15.4)),
        patch(
            "core.tts.router.TTSRouter.status",
            return_value={"engine": "piper", "loaded": True, "model_id": "es_ES"},
        ),
    ):
        res = client.post(
            "/api/v1/tts/load",
            json={"engine": "piper", "lang": "es"},
            headers=teacher_headers,
        )
    assert res.status_code == 202
    data = res.json()
    assert data["engine"] == "piper"
    assert data["loaded"] is True
    assert data["model_id"] == "es_ES"
    assert data["load_ms"] == 15.4


def test_tts_load_unavailable_returns_503(
    client: TestClient, teacher_headers: dict[str, str]
) -> None:
    """Verifies POST /api/v1/tts/load returns 503 when the engine is not installed."""
    with patch(
        "core.tts.router.TTSRouter.preload",
        side_effect=TTSUnavailableError("Model missing"),
    ):
        res = client.post(
            "/api/v1/tts/load",
            json={"engine": "nonexistent", "lang": "es"},
            headers=teacher_headers,
        )
    assert res.status_code == 503
    assert "Model missing" in res.json()["detail"]


def test_tts_load_forbidden_for_student(
    client: TestClient, student_headers: dict[str, str]
) -> None:
    """Verifies POST /api/v1/tts/load returns 403 Forbidden for student users."""
    res = client.post(
        "/api/v1/tts/load",
        json={"engine": "piper", "lang": "es"},
        headers=student_headers,
    )
    assert res.status_code == 403


def test_tts_unload_success(
    client: TestClient, teacher_headers: dict[str, str]
) -> None:
    """Verifies POST /api/v1/tts/unload returns 200 with loaded=False."""
    with patch("core.tts.router.TTSRouter.unload", return_value="piper"):
        res = client.post(
            "/api/v1/tts/unload",
            json={"engine": "piper"},
            headers=teacher_headers,
        )
    assert res.status_code == 200
    data = res.json()
    assert data["engine"] == "piper"
    assert data["loaded"] is False


def test_tts_status_success(
    client: TestClient, teacher_headers: dict[str, str]
) -> None:
    """Verifies GET /api/v1/tts/status returns current engine readiness."""
    with patch(
        "core.tts.router.TTSRouter.status",
        return_value={"engine": "piper", "loaded": True, "model_id": "model.onnx"},
    ):
        res = client.get(
            "/api/v1/tts/status?engine=piper&lang=es",
            headers=teacher_headers,
        )
    assert res.status_code == 200
    data = res.json()
    assert data["engine"] == "piper"
    assert data["loaded"] is True
    assert data["model_id"] == "model.onnx"


def test_tts_status_not_found(
    client: TestClient, teacher_headers: dict[str, str]
) -> None:
    """Verifies GET /api/v1/tts/status returns 404 for unknown/unavailable engine."""
    with patch(
        "core.tts.router.TTSRouter.status",
        side_effect=TTSUnavailableError("Unknown engine"),
    ):
        res = client.get(
            "/api/v1/tts/status?engine=invalid",
            headers=teacher_headers,
        )
    assert res.status_code == 404


def test_tts_voices_listing(
    client: TestClient, teacher_headers: dict[str, str], monkeypatch
) -> None:
    """Verifies GET /api/v1/tts/voices lists configured voices for Spanish and K'iche'."""
    res_es = client.get("/api/v1/tts/voices?lang=es", headers=teacher_headers)
    assert res_es.status_code == 200
    voices_es = res_es.json()
    assert len(voices_es) >= 2
    assert any(v["engine"] == "piper" for v in voices_es)
    assert any(v["engine"] == "espeak" for v in voices_es)
    assert any(v["engine"] == "sherpa" for v in voices_es)
    assert any(v["engine"] == "kokoro" for v in voices_es)
    assert any(v["engine"] == "qwen3-tts" for v in voices_es)

    res_sherpa = client.get(
        "/api/v1/tts/voices?lang=es&engine=sherpa", headers=teacher_headers
    )
    assert res_sherpa.status_code == 200
    assert len(res_sherpa.json()) == 1
    assert res_sherpa.json()[0]["engine"] == "sherpa"

    res_qwen = client.get(
        "/api/v1/tts/voices?lang=es&engine=qwen3-tts", headers=teacher_headers
    )
    assert res_qwen.status_code == 200
    assert len(res_qwen.json()) == 1
    assert res_qwen.json()[0]["engine"] == "qwen3-tts"

    res_quc = client.get("/api/v1/tts/voices?lang=quc", headers=teacher_headers)
    assert res_quc.status_code == 200
    voices_quc = res_quc.json()
    assert any(v["lang"] == "quc" for v in voices_quc)

    # When voice_quc is configured for espeak
    monkeypatch.setenv("TTS_VOICE_QUC", "quc-voice")
    from core.config import clear_settings_cache

    clear_settings_cache()
    res_quc_with_espeak = client.get(
        "/api/v1/tts/voices?lang=quc", headers=teacher_headers
    )
    assert res_quc_with_espeak.status_code == 200
    assert any(
        v["engine"] == "espeak" and v["id"] == "quc-voice"
        for v in res_quc_with_espeak.json()
    )
