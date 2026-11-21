"""Integration tests for the >51% explanation in the Mayan languages (MMS voices)."""

import pytest

from api.session.speech import clear_speech_cache
from core.config import clear_settings_cache
from core.tts import get_tts_router
from tests.api.session.test_session_speech import FAKE_WAV, _play_b_round, _speech


@pytest.fixture(autouse=True)
def _empty_speech_cache():
    clear_settings_cache()
    clear_speech_cache()
    yield
    clear_settings_cache()
    clear_speech_cache()


@pytest.mark.parametrize("lang", ["quc", "kek"])
def test_mayan_speech_uses_the_mms_voice(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch, lang
):
    """Verifies the explanation is spoken by the MMS voice of the requested language."""
    _, conn = staff_db
    mms = get_tts_router().get_backend("mms")
    spoken: dict[str, str] = {}
    monkeypatch.setattr(mms, "is_available", lambda voice=None: voice == lang)
    monkeypatch.setattr(
        mms,
        "synthesize",
        lambda text, voice=None: (
            spoken.update(text=text, voice=voice or "") or FAKE_WAV
        ),
    )
    sid = _play_b_round(client, conn, teacher_headers)

    response = _speech(client, sid, teacher_headers, lang=lang)

    assert response.status_code == 200
    assert response.content == FAKE_WAV
    assert spoken["voice"] == lang
    assert spoken["text"].startswith("Atención:")  # the Spanish explanation text


def test_qeqchi_speech_without_a_voice_is_unavailable(
    staff_db, client, teacher_headers
):
    """Verifies Qʼeqchiʼ answers 503 instead of speaking with a Spanish voice."""
    _, conn = staff_db
    sid = _play_b_round(client, conn, teacher_headers)

    response = _speech(client, sid, teacher_headers, lang="kek")

    assert response.status_code == 503
    assert "kek" in response.json()["detail"]
