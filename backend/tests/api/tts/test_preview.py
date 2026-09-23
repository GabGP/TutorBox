"""Integration tests for POST /api/v1/tts/preview."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from core.tts.exceptions import TTSUnavailableError
from core.tts.router import get_tts_router

FAKE_WAV = b"RIFFfake-wav-bytes"


def _patch_router(monkeypatch, *, loaded: bool, wav: bytes | None = FAKE_WAV):
    """Patches the singleton instance (class patches are shadowed once an
    earlier suite pins an instance attribute on the shared router)."""
    router = get_tts_router()
    monkeypatch.setattr(
        router,
        "status",
        lambda engine=None, lang="es": {
            "engine": "piper",
            "loaded": loaded,
            "model_id": "m",
        },
    )
    if isinstance(wav, Exception):

        def _raise(*args, **kwargs):
            raise wav

        monkeypatch.setattr(router, "synthesize", _raise)
        synth_mock = None
    else:
        synth_mock = MagicMock(return_value=wav)
        monkeypatch.setattr(router, "synthesize", synth_mock)
    unload_mock = MagicMock(return_value="piper")
    monkeypatch.setattr(router, "unload", unload_mock)
    return unload_mock, synth_mock


def test_tts_preview_unloads_when_engine_was_idle(
    client: TestClient, teacher_headers: dict[str, str], monkeypatch
) -> None:
    """Preview auto-unloads afterwards so no weights linger in RAM."""
    unload, synth = _patch_router(monkeypatch, loaded=False)
    res = client.post(
        "/api/v1/tts/preview",
        json={"engine": "piper", "lang": "es"},
        headers=teacher_headers,
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
    assert res.content == FAKE_WAV
    unload.assert_called_once_with(engine="piper")
    assert synth is not None
    synth.assert_called_once_with(
        "Hola, esta es la voz de TutorBox para tu clase.",
        lang="es",
        voice=None,
        backend="piper",
        bypass_cache=True,
    )


def test_tts_preview_keeps_already_loaded_engine(
    client: TestClient, teacher_headers: dict[str, str], monkeypatch
) -> None:
    """Preview leaves a resident engine loaded for the live game."""
    unload, _synth = _patch_router(monkeypatch, loaded=True)
    res = client.post(
        "/api/v1/tts/preview",
        json={"lang": "es"},
        headers=teacher_headers,
    )
    assert res.status_code == 200
    unload.assert_not_called()


def test_tts_preview_unavailable_returns_503(
    client: TestClient, teacher_headers: dict[str, str], monkeypatch
) -> None:
    """Preview maps synthesis failures to 503 without leaking the engine."""
    unload, _synth = _patch_router(
        monkeypatch, loaded=False, wav=TTSUnavailableError("No voice")
    )
    res = client.post(
        "/api/v1/tts/preview",
        json={"lang": "es"},
        headers=teacher_headers,
    )
    assert res.status_code == 503
    unload.assert_called_once_with(engine="piper")


def test_tts_preview_forbidden_for_student(
    client: TestClient, student_headers: dict[str, str]
) -> None:
    """Students cannot trigger synthesis jobs on the appliance."""
    res = client.post(
        "/api/v1/tts/preview",
        json={"lang": "es"},
        headers=student_headers,
    )
    assert res.status_code == 403


def test_tts_preview_status_unavailable_returns_404(
    client: TestClient, teacher_headers: dict[str, str], monkeypatch
) -> None:
    """Preview maps status resolution failure to 404."""
    router = get_tts_router()

    def _raise_status(*args, **kwargs):
        raise TTSUnavailableError("Unknown engine")

    monkeypatch.setattr(router, "status", _raise_status)
    res = client.post(
        "/api/v1/tts/preview",
        json={"engine": "unknown", "lang": "es"},
        headers=teacher_headers,
    )
    assert res.status_code == 404


def test_tts_preview_synthesis_error_returns_500(
    client: TestClient, teacher_headers: dict[str, str], monkeypatch
) -> None:
    """Preview maps unexpected TTSError to 500."""
    from core.tts.exceptions import TTSSynthesisError

    unload, _synth = _patch_router(
        monkeypatch, loaded=False, wav=TTSSynthesisError("Crash")
    )
    res = client.post(
        "/api/v1/tts/preview",
        json={"lang": "es"},
        headers=teacher_headers,
    )
    assert res.status_code == 500
    unload.assert_called_once_with(engine="piper")
