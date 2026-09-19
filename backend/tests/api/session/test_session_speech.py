"""Integration tests for the spoken >51% intervention endpoint."""

import pytest

from api.session.speech import clear_speech_cache
from core.config import clear_settings_cache
from core.db.question_repository import create_question
from core.tts import TTSSynthesisError, TTSUnavailableError, get_tts_router
from modes.quiz.contracts import DistractorDetail, QuizQuestionCreate
from tests.conftest import auth_headers

FAKE_WAV = b"RIFF\x24\x00\x00\x00WAVEfmt fake-audio"


CLEAN_VARS = (
    "TTS_ENABLED",
    "TTS_ENGINE",
    "TTS_VOICE",
    "TTS_VOICE_QUC",
    "TTS_ESPEAK_BINARY",
)


@pytest.fixture(autouse=True)
def _clean_tts_settings(monkeypatch: pytest.MonkeyPatch):
    """Runs every test against clean settings and an empty speech cache."""
    for name in CLEAN_VARS:
        monkeypatch.delenv(name, raising=False)
    clear_settings_cache()
    clear_speech_cache()
    yield
    clear_settings_cache()
    clear_speech_cache()


def _seed_question(conn) -> str:
    """Seeds a test fractions question with diagnostic distractors and returns its ID."""
    distractors = {
        "B": DistractorDetail(
            misconception="halved_num",
            explanation="Dividiste sólo el numerador entre 2.",
        ),
        "C": DistractorDetail(
            misconception="wrong_factor", explanation="Usaste el factor equivocado."
        ),
        "D": DistractorDetail(
            misconception="kept_denom", explanation="Conservaste el denominador."
        ),
    }
    q = QuizQuestionCreate(
        topic="fractions",
        subconcept="simplification",
        question_text="¿Cuál es 6/8 simplificado?",
        options={"A": "3/4", "B": "1/2", "C": "2/3", "D": "5/8"},
        correct_option="A",
        distractors=distractors,
    )
    qid = create_question(conn, q)
    conn.commit()
    return qid


def _play_round(
    client,
    conn,
    teacher,
    votes: dict[str, str],
    close: bool = True,
    reveal: bool = True,
) -> str:
    """Creates a one-question match, collects the given votes, and reveals it."""
    qid = _seed_question(conn)
    res = client.post(
        "/api/v1/session",
        json={"title": "Voz", "topic": "fractions", "question_ids": [qid]},
        headers=teacher,
    )
    sid = res.json()["id"]
    client.post(f"/api/v1/session/{sid}/start", headers=teacher)
    for username, option in votes.items():
        client.post(
            f"/api/v1/session/{sid}/vote",
            json={"selected_option": option},
            headers=auth_headers(client, username),
        )
    if close:
        client.post(f"/api/v1/session/{sid}/close", headers=teacher)
    if reveal:
        client.post(f"/api/v1/session/{sid}/reveal", headers=teacher)
    return sid


def _play_b_round(
    client, conn, teacher, close: bool = True, reveal: bool = True
) -> str:
    """Creates and plays a round where students vote exclusively for distractor B."""
    return _play_round(
        client,
        conn,
        teacher,
        {"student1": "B", "student2": "B"},
        close=close,
        reveal=reveal,
    )


def _speech(client, sid: str, hdrs: dict, lang: str | None = None):
    """Convenience helper to request round speech."""
    url = f"/api/v1/session/{sid}/speech" + (f"?lang={lang}" if lang else "")
    return client.get(url, headers=hdrs)


def test_speech_returns_wav_when_one_wrong_answer_passes_51_percent(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies a shared misconception is synthesized in Latin American Spanish."""
    _, conn = staff_db
    spoken: dict[str, str] = {}

    def fake_synthesize(text: str, lang: str = "es") -> bytes:
        spoken.update({"text": text, "lang": lang})
        return FAKE_WAV

    monkeypatch.setattr("api.session.speech.synthesize_speech", fake_synthesize)
    sid = _play_b_round(client, conn, teacher_headers)

    res = _speech(client, sid, teacher_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
    assert res.content == FAKE_WAV
    assert spoken["lang"] == "es"
    assert "100 por ciento del grupo respondió 1/2" in spoken["text"]
    assert "Dividiste sólo el numerador entre 2." in spoken["text"]
    assert spoken["text"].endswith("La respuesta correcta es 3/4.")


def test_speech_is_refused_when_the_rule_did_not_trigger(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies a split class stays silent: no synthesis, no audio."""
    _, conn = staff_db
    calls: list[str] = []
    monkeypatch.setattr(
        "api.session.speech.synthesize_speech",
        lambda text, lang="es": calls.append(text) or FAKE_WAV,
    )
    sid = _play_round(client, conn, teacher_headers, {"student1": "A", "student2": "B"})

    res = _speech(client, sid, teacher_headers)
    assert res.status_code == 409
    assert "did not trigger" in res.json()["detail"]
    assert calls == []


def test_speech_rejects_open_active_round(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies audio synthesis is refused while students are actively voting."""
    _, conn = staff_db
    monkeypatch.setattr(
        "api.session.speech.synthesize_speech", lambda t, lang="es": FAKE_WAV
    )
    sid = _play_b_round(client, conn, teacher_headers, close=False, reveal=False)

    res = _speech(client, sid, teacher_headers)
    assert res.status_code == 409
    assert "voting has not finished" in res.json()["detail"]


def test_speech_allows_speculative_prefetch_on_closed_round(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies speculative pre-fetch succeeds once round is closed before reveal."""
    _, conn = staff_db
    monkeypatch.setattr(
        "api.session.speech.synthesize_speech", lambda t, lang="es": FAKE_WAV
    )
    sid = _play_b_round(client, conn, teacher_headers, close=True, reveal=False)

    res = _speech(client, sid, teacher_headers)
    assert res.status_code == 200 and res.content == FAKE_WAV


def test_speech_is_teacher_only(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies student devices cannot pull the spoken explanation."""
    _, conn = staff_db
    monkeypatch.setattr(
        "api.session.speech.synthesize_speech", lambda t, lang="es": FAKE_WAV
    )
    sid = _play_b_round(client, conn, teacher_headers)

    res = _speech(client, sid, auth_headers(client, "student1"))
    assert res.status_code == 403


def test_speech_unknown_session_is_404(staff_db, client, teacher_headers):
    """Verifies a stale session id does not reach the synthesizer."""
    assert _speech(client, "s_missing", teacher_headers).status_code == 404


def test_speech_reports_a_missing_speech_engine(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies an appliance without speech engine answers 503 with the install hint."""
    _, conn = staff_db

    def fake_synthesize(text: str, lang: str = "es") -> bytes:
        raise TTSUnavailableError(
            "espeak is not installed... sudo apt install espeak-ng"
        )

    monkeypatch.setattr("api.session.speech.synthesize_speech", fake_synthesize)
    sid = _play_b_round(client, conn, teacher_headers)

    res = _speech(client, sid, teacher_headers)
    assert res.status_code == 503
    assert "espeak-ng" in res.json()["detail"]


def test_speech_reports_a_failing_engine(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies a synthesis crash is a server error, not a silent empty file."""
    _, conn = staff_db

    def fake_synthesize(text: str, lang: str = "es") -> bytes:
        raise TTSSynthesisError("Engine exited with code 1")

    monkeypatch.setattr("api.session.speech.synthesize_speech", fake_synthesize)
    sid = _play_b_round(client, conn, teacher_headers)

    assert _speech(client, sid, teacher_headers).status_code == 500


def test_speech_in_kiche_behavior(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies K'iche' voice failure without voice, and success with voice configured."""
    _, conn = staff_db
    router = get_tts_router()
    monkeypatch.setattr(router.piper, "is_available", lambda voice=None: False)
    sid = _play_b_round(client, conn, teacher_headers)

    res_unavail = _speech(client, sid, teacher_headers, lang="quc")
    assert res_unavail.status_code == 503 and "quc" in res_unavail.json()["detail"]

    monkeypatch.setenv("TTS_VOICE_QUC", "quc-test")
    clear_settings_cache()
    monkeypatch.setattr(router.espeak, "is_available", lambda voice=None: True)
    used: dict[str, str] = {}
    monkeypatch.setattr(
        router.espeak,
        "synthesize",
        lambda t, voice=None: used.update({"voice": voice or ""}) or FAKE_WAV,
    )

    res_avail = _speech(client, sid, teacher_headers, lang="quc")
    assert res_avail.status_code == 200 and used["voice"] == "quc-test"


def test_speech_rejects_an_unknown_language(staff_db, client, teacher_headers):
    """Verifies only the classroom languages are accepted."""
    assert _speech(client, "s_any", teacher_headers, lang="fr").status_code == 422


def test_speech_without_the_round_question_is_404(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies a round whose question vanished reports 404 instead of speaking nothing."""
    _, conn = staff_db
    sid = _play_b_round(client, conn, teacher_headers)
    monkeypatch.setattr("api.session.speech.get_question_by_id", lambda conn, qid: None)
    res = _speech(client, sid, teacher_headers)
    assert res.status_code == 404 and "Question" in res.json()["detail"]


def test_speech_returns_cached_audio_on_subsequent_calls(
    staff_db, client, teacher_headers, monkeypatch: pytest.MonkeyPatch
):
    """Verifies that repeatedly calling /speech returns cached audio."""
    _, conn = staff_db
    calls: list[str] = []
    router = get_tts_router()
    router.clear_cache()
    for engine in (router.qwen, router.kokoro, router.sherpa, router.piper):
        monkeypatch.setattr(engine, "is_available", lambda voice=None: False)
    monkeypatch.setattr(router.espeak, "is_available", lambda voice=None: True)
    monkeypatch.setattr(
        router.espeak, "synthesize", lambda t, voice=None: calls.append(t) or FAKE_WAV
    )

    sid = _play_b_round(client, conn, teacher_headers)
    assert _speech(client, sid, teacher_headers).status_code == 200
    assert _speech(client, sid, teacher_headers).status_code == 200
    assert len(calls) == 1
