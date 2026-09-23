"""Integration tests for voice selection on the >51% speech endpoint."""

from unittest.mock import ANY, MagicMock

import pytest
from fastapi.testclient import TestClient
from test_session_speech import FAKE_WAV, _play_b_round

from core.tts.router import get_tts_router


def test_speech_honors_saved_voice_engine_and_voice(
    staff_db, client: TestClient, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies ?engine=&voice= route synthesis to the teacher's saved voice."""
    _, conn = staff_db
    router = get_tts_router()
    synth_mock = MagicMock(return_value=FAKE_WAV)
    monkeypatch.setattr(router, "synthesize", synth_mock)

    sid = _play_b_round(client, conn, teacher_headers)
    res = client.get(
        f"/api/v1/session/{sid}/speech?lang=es&engine=piper&voice=voz-x",
        headers=teacher_headers,
    )
    assert res.status_code == 200
    assert res.content == FAKE_WAV
    synth_mock.assert_called_once_with(ANY, lang="es", voice="voz-x", backend="piper")


def test_speech_defaults_to_configured_engine_without_params(
    staff_db, client: TestClient, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies the legacy path still delegates to synthesize_speech."""
    _, conn = staff_db
    monkeypatch.setattr(
        "api.session.speech.synthesize_speech", lambda t, lang="es": FAKE_WAV
    )

    sid = _play_b_round(client, conn, teacher_headers)
    res = client.get(f"/api/v1/session/{sid}/speech", headers=teacher_headers)
    assert res.status_code == 200
    assert res.content == FAKE_WAV
