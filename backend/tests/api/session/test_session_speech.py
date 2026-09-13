"""Integration tests for the spoken >51% intervention endpoint.

espeak is not installed in CI, so synthesis is faked; what these tests pin down is that audio
is only ever produced when a single distractor really passed the rule, and that a classroom
without the engine gets a clear 503 instead of a broken reveal screen.
"""

import pytest

from core.config import clear_settings_cache
from core.db.question_repository import create_question
from core.tts import TTSSynthesisError, TTSUnavailableError
from modes.quiz.contracts.models import DistractorDetail, QuizQuestionCreate
from tests.conftest import auth_headers

FAKE_WAV = b"RIFF\x24\x00\x00\x00WAVEfmt fake-audio"


@pytest.fixture(autouse=True)
def _clean_tts_settings(monkeypatch: pytest.MonkeyPatch):
    """Runs every test against the shipped espeak defaults (es-419, no K'iche')."""
    for name in ("TTS_ENABLED", "TTS_VOICE", "TTS_VOICE_QUC", "TTS_ESPEAK_BINARY"):
        monkeypatch.delenv(name, raising=False)
    clear_settings_cache()
    yield
    clear_settings_cache()


def _seed_question(conn) -> str:
    question_id = create_question(
        conn,
        QuizQuestionCreate(
            topic="fractions",
            subconcept="simplification",
            question_text="¿Cuál es 6/8 simplificado?",
            options={"A": "3/4", "B": "1/2", "C": "2/3", "D": "5/8"},
            correct_option="A",
            distractors={
                "B": DistractorDetail(
                    misconception="halved_numerator_only",
                    explanation="Dividiste sólo el numerador entre 2.",
                ),
                "C": DistractorDetail(
                    misconception="wrong_factor",
                    explanation="Usaste el factor equivocado.",
                ),
                "D": DistractorDetail(
                    misconception="kept_denominator",
                    explanation="Conservaste el denominador.",
                ),
            },
        ),
    )
    conn.commit()
    return question_id


def _play_round(client, conn, votes: dict[str, str], reveal: bool = True) -> str:
    """Creates a one-question match, collects the given votes, and reveals it."""
    question_id = _seed_question(conn)
    teacher = auth_headers(client, "teacher1")
    session_id = client.post(
        "/api/v1/session",
        json={
            "title": "Voz",
            "topic": "fractions",
            "question_ids": [question_id],
        },
        headers=teacher,
    ).json()["id"]
    client.post(f"/api/v1/session/{session_id}/start", headers=teacher)
    for username, option in votes.items():
        client.post(
            f"/api/v1/session/{session_id}/vote",
            json={"selected_option": option},
            headers=auth_headers(client, username),
        )
    client.post(f"/api/v1/session/{session_id}/close", headers=teacher)
    if reveal:
        client.post(f"/api/v1/session/{session_id}/reveal", headers=teacher)
    return session_id


def test_speech_returns_wav_when_one_wrong_answer_passes_51_percent(
    staff_db, client, monkeypatch: pytest.MonkeyPatch
):
    """Verifies a shared misconception is synthesized in Latin American Spanish."""
    _, conn = staff_db
    spoken: dict[str, str] = {}

    def fake_synthesize(text: str, voice: str | None = None) -> bytes:
        spoken["text"] = text
        spoken["voice"] = voice or ""
        return FAKE_WAV

    monkeypatch.setattr("api.session.speech.synthesize_wav", fake_synthesize)
    session_id = _play_round(client, conn, {"student1": "B", "student2": "B"})

    response = client.get(
        f"/api/v1/session/{session_id}/speech",
        headers=auth_headers(client, "teacher1"),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == FAKE_WAV
    assert spoken["voice"] == "es-419"
    assert "100 por ciento del grupo respondió 1/2" in spoken["text"]
    assert "Dividiste sólo el numerador entre 2." in spoken["text"]
    assert spoken["text"].endswith("La respuesta correcta es 3/4.")


def test_speech_is_refused_when_the_rule_did_not_trigger(
    staff_db, client, monkeypatch: pytest.MonkeyPatch
):
    """Verifies a split class stays silent: no synthesis, no audio."""
    _, conn = staff_db
    calls: list[str] = []
    monkeypatch.setattr(
        "api.session.speech.synthesize_wav",
        lambda text, voice=None: calls.append(text) or FAKE_WAV,
    )
    session_id = _play_round(client, conn, {"student1": "A", "student2": "B"})

    response = client.get(
        f"/api/v1/session/{session_id}/speech",
        headers=auth_headers(client, "teacher1"),
    )

    assert response.status_code == 409
    assert "did not trigger" in response.json()["detail"]
    assert calls == []


def test_speech_requires_a_revealed_round(
    staff_db, client, monkeypatch: pytest.MonkeyPatch
):
    """Verifies the explanation cannot leak before the teacher reveals the answer."""
    _, conn = staff_db
    monkeypatch.setattr(
        "api.session.speech.synthesize_wav", lambda text, voice=None: FAKE_WAV
    )
    session_id = _play_round(
        client, conn, {"student1": "B", "student2": "B"}, reveal=False
    )

    response = client.get(
        f"/api/v1/session/{session_id}/speech",
        headers=auth_headers(client, "teacher1"),
    )

    assert response.status_code == 409
    assert "not been revealed" in response.json()["detail"]


def test_speech_is_teacher_only(staff_db, client, monkeypatch: pytest.MonkeyPatch):
    """Verifies student devices cannot pull the spoken explanation."""
    _, conn = staff_db
    monkeypatch.setattr(
        "api.session.speech.synthesize_wav", lambda text, voice=None: FAKE_WAV
    )
    session_id = _play_round(client, conn, {"student1": "B", "student2": "B"})

    response = client.get(
        f"/api/v1/session/{session_id}/speech",
        headers=auth_headers(client, "student1"),
    )

    assert response.status_code == 403


def test_speech_unknown_session_is_404(staff_db, client):
    """Verifies a stale session id does not reach the synthesizer."""
    response = client.get(
        "/api/v1/session/s_missing/speech",
        headers=auth_headers(client, "teacher1"),
    )

    assert response.status_code == 404


def test_speech_reports_a_missing_espeak_engine(
    staff_db, client, monkeypatch: pytest.MonkeyPatch
):
    """Verifies an appliance without espeak answers 503 with the install hint."""
    _, conn = staff_db

    def fake_synthesize(text: str, voice: str | None = None) -> bytes:
        raise TTSUnavailableError(
            "espeak is not installed... sudo apt install espeak-ng"
        )

    monkeypatch.setattr("api.session.speech.synthesize_wav", fake_synthesize)
    session_id = _play_round(client, conn, {"student1": "B", "student2": "B"})

    response = client.get(
        f"/api/v1/session/{session_id}/speech",
        headers=auth_headers(client, "teacher1"),
    )

    assert response.status_code == 503
    assert "espeak-ng" in response.json()["detail"]


def test_speech_reports_a_failing_engine(
    staff_db, client, monkeypatch: pytest.MonkeyPatch
):
    """Verifies a synthesis crash is a server error, not a silent empty file."""
    _, conn = staff_db

    def fake_synthesize(text: str, voice: str | None = None) -> bytes:
        raise TTSSynthesisError("espeak exited with code 1")

    monkeypatch.setattr("api.session.speech.synthesize_wav", fake_synthesize)
    session_id = _play_round(client, conn, {"student1": "B", "student2": "B"})

    response = client.get(
        f"/api/v1/session/{session_id}/speech",
        headers=auth_headers(client, "teacher1"),
    )

    assert response.status_code == 500


def test_speech_in_kiche_is_unavailable_until_a_voice_is_configured(
    staff_db, client, monkeypatch: pytest.MonkeyPatch
):
    """Verifies the K'iche' toggle reports honestly instead of speaking Spanish."""
    _, conn = staff_db
    calls: list[str] = []
    monkeypatch.setattr(
        "api.session.speech.synthesize_wav",
        lambda text, voice=None: calls.append(text) or FAKE_WAV,
    )
    session_id = _play_round(client, conn, {"student1": "B", "student2": "B"})

    response = client.get(
        f"/api/v1/session/{session_id}/speech?lang=quc",
        headers=auth_headers(client, "teacher1"),
    )

    assert response.status_code == 503
    assert "quc" in response.json()["detail"]
    assert calls == []


def test_speech_uses_the_configured_kiche_voice_when_present(
    staff_db, client, monkeypatch: pytest.MonkeyPatch
):
    """Verifies TTS_VOICE_QUC routes the K'iche' request to that espeak voice."""
    _, conn = staff_db
    monkeypatch.setenv("TTS_VOICE_QUC", "quc-test")
    clear_settings_cache()
    used: dict[str, str] = {}

    def fake_synthesize(text: str, voice: str | None = None) -> bytes:
        used["voice"] = voice or ""
        return FAKE_WAV

    monkeypatch.setattr("api.session.speech.synthesize_wav", fake_synthesize)
    session_id = _play_round(client, conn, {"student1": "B", "student2": "B"})

    response = client.get(
        f"/api/v1/session/{session_id}/speech?lang=quc",
        headers=auth_headers(client, "teacher1"),
    )

    assert response.status_code == 200
    assert used["voice"] == "quc-test"


def test_speech_rejects_an_unknown_language(staff_db, client):
    """Verifies only the classroom languages are accepted."""
    response = client.get(
        "/api/v1/session/s_any/speech?lang=fr",
        headers=auth_headers(client, "teacher1"),
    )

    assert response.status_code == 422


def test_speech_without_the_round_question_is_404(
    staff_db, client, monkeypatch: pytest.MonkeyPatch
):
    """Verifies a round whose question vanished reports 404 instead of speaking nothing."""
    _, conn = staff_db
    monkeypatch.setattr(
        "api.session.speech.synthesize_wav", lambda text, voice=None: FAKE_WAV
    )
    session_id = _play_round(client, conn, {"student1": "B", "student2": "B"})
    monkeypatch.setattr("api.session.speech.get_question_by_id", lambda conn, qid: None)

    response = client.get(
        f"/api/v1/session/{session_id}/speech",
        headers=auth_headers(client, "teacher1"),
    )

    assert response.status_code == 404
    assert "Question" in response.json()["detail"]
