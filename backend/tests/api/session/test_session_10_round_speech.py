"""End-to-end 10-round classroom match simulation validating voice feedback gating.

Verifies the deterministic >51% distractor rule, silence on ties / majority correct,
bilingual speech dispatch (Spanish & K'iche'), and first-press locking across 10 rounds.
"""

from collections.abc import Sequence

import pytest

from api.session.speech import clear_speech_cache
from core.config import clear_settings_cache
from core.db.question_repository import create_question
from core.tts.router import get_tts_router
from modes.quiz.contracts.models import DistractorDetail, QuizQuestionCreate
from tests.conftest import PRE_HASHED_PIN_1234, auth_headers

FAKE_WAV = b"RIFF\x24\x00\x00\x00WAVEfmt fake-audio-stream"


@pytest.fixture(autouse=True)
def _setup_tts(monkeypatch: pytest.MonkeyPatch):
    """Sets up clean environment and mocks synthesizer for CI execution."""
    clear_settings_cache()
    clear_speech_cache()
    router = get_tts_router()
    router.clear_cache()
    monkeypatch.setattr(
        router, "synthesize", lambda text, lang="es", voice=None: FAKE_WAV
    )
    yield
    clear_settings_cache()
    clear_speech_cache()


def _seed_10_questions(conn) -> list[str]:
    """Creates 10 distinct diagnostic questions and seeds additional students."""
    cursor = conn.cursor()
    extra_students = [
        ("student3", PRE_HASHED_PIN_1234, "student"),
        ("student4", PRE_HASHED_PIN_1234, "student"),
        ("student5", PRE_HASHED_PIN_1234, "student"),
    ]
    cursor.executemany(
        "INSERT INTO users (username, hashed_pin, role) VALUES (?, ?, ?)",
        extra_students,
    )

    qids = []
    for i in range(1, 11):
        distractors = {
            "B": DistractorDetail(
                misconception="err_b", explanation=f"Error B en pregunta {i}"
            ),
            "C": DistractorDetail(
                misconception="err_c", explanation=f"Error C en pregunta {i}"
            ),
            "D": DistractorDetail(
                misconception="err_d", explanation=f"Error D en pregunta {i}"
            ),
        }
        qid = create_question(
            conn,
            QuizQuestionCreate(
                topic="math",
                subconcept="fractions",
                question_text=f"Pregunta diagnóstica {i}?",
                options={
                    "A": f"Correcto {i}",
                    "B": f"Opción B {i}",
                    "C": f"Opción C {i}",
                    "D": f"Opción D {i}",
                },
                correct_option="A",
                distractors=distractors,
            ),
        )
        qids.append(qid)
    conn.commit()
    return qids


def _cast_votes(client, sid: str, votes: Sequence[tuple[str, str]]) -> None:
    """Submits a sequence of (student_username, option) votes."""
    for username, option in votes:
        res = client.post(
            f"/api/v1/session/{sid}/vote",
            json={"selected_option": option},
            headers=auth_headers(client, username),
        )
        assert res.status_code == 200


def test_ten_round_classroom_match_simulation(staff_db, client, teacher_headers):
    """Simulates a complete 10-question classroom match proving deterministic voice gating."""
    _, conn = staff_db
    qids = _seed_10_questions(conn)

    # 1. Create match with 10 questions
    res = client.post(
        "/api/v1/session",
        json={"title": "10-Round Match", "topic": "math", "question_ids": qids},
        headers=teacher_headers,
    )
    assert res.status_code == 201
    sid = res.json()["id"]

    # --- Round 1: 5/5 = 100% Distractor B (>51%) -> SPEAKS Spanish ---
    client.post(f"/api/v1/session/{sid}/start", headers=teacher_headers)
    _cast_votes(
        client,
        sid,
        [
            ("student1", "B"),
            ("student2", "B"),
            ("student3", "B"),
            ("student4", "B"),
            ("student5", "B"),
        ],
    )
    client.post(f"/api/v1/session/{sid}/close", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher_headers)
    r1 = client.get(f"/api/v1/session/{sid}/speech?lang=es", headers=teacher_headers)
    assert r1.status_code == 200 and r1.content == FAKE_WAV

    # --- Round 2: 3/5 = 60% Distractor C (>51%) -> SPEAKS Spanish ---
    client.post(f"/api/v1/session/{sid}/next", headers=teacher_headers)
    _cast_votes(
        client,
        sid,
        [
            ("student1", "C"),
            ("student2", "C"),
            ("student3", "C"),
            ("student4", "A"),
            ("student5", "B"),
        ],
    )
    client.post(f"/api/v1/session/{sid}/close", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher_headers)
    r2 = client.get(f"/api/v1/session/{sid}/speech?lang=es", headers=teacher_headers)
    assert r2.status_code == 200 and r2.content == FAKE_WAV

    # --- Round 3: 5/5 = 100% Correct A -> SILENT (409) ---
    client.post(f"/api/v1/session/{sid}/next", headers=teacher_headers)
    _cast_votes(
        client,
        sid,
        [
            ("student1", "A"),
            ("student2", "A"),
            ("student3", "A"),
            ("student4", "A"),
            ("student5", "A"),
        ],
    )
    client.post(f"/api/v1/session/{sid}/close", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher_headers)
    r3 = client.get(f"/api/v1/session/{sid}/speech?lang=es", headers=teacher_headers)
    assert r3.status_code == 409 and "did not trigger" in r3.json()["detail"]

    # --- Round 4: Dispersed wrong votes (2 B, 2 C, 1 D = 40%, 40%, 20%) -> SILENT (409) ---
    client.post(f"/api/v1/session/{sid}/next", headers=teacher_headers)
    _cast_votes(
        client,
        sid,
        [
            ("student1", "B"),
            ("student2", "B"),
            ("student3", "C"),
            ("student4", "C"),
            ("student5", "D"),
        ],
    )
    client.post(f"/api/v1/session/{sid}/close", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher_headers)
    r4 = client.get(f"/api/v1/session/{sid}/speech?lang=es", headers=teacher_headers)
    assert r4.status_code == 409

    # --- Round 5: Majority correct (3 A = 60%, 2 B = 40%) -> SILENT (409) ---
    client.post(f"/api/v1/session/{sid}/next", headers=teacher_headers)
    _cast_votes(
        client,
        sid,
        [
            ("student1", "A"),
            ("student2", "A"),
            ("student3", "A"),
            ("student4", "B"),
            ("student5", "B"),
        ],
    )
    client.post(f"/api/v1/session/{sid}/close", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher_headers)
    r5 = client.get(f"/api/v1/session/{sid}/speech?lang=es", headers=teacher_headers)
    assert r5.status_code == 409

    # --- Round 6: 50% / 50% split (1 B, 1 C <= 51%) -> SILENT (409) ---
    client.post(f"/api/v1/session/{sid}/next", headers=teacher_headers)
    _cast_votes(client, sid, [("student1", "B"), ("student2", "C")])
    client.post(f"/api/v1/session/{sid}/close", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher_headers)
    r6 = client.get(f"/api/v1/session/{sid}/speech?lang=es", headers=teacher_headers)
    assert r6.status_code == 409

    # --- Round 7: Zero votes submitted (timeout) -> SILENT (409) ---
    client.post(f"/api/v1/session/{sid}/next", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/close", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher_headers)
    r7 = client.get(f"/api/v1/session/{sid}/speech?lang=es", headers=teacher_headers)
    assert r7.status_code == 409

    # --- Round 8: 4/5 = 80% Distractor D (>51%) with K'ICHE' request -> SPEAKS K'iche' ---
    client.post(f"/api/v1/session/{sid}/next", headers=teacher_headers)
    _cast_votes(
        client,
        sid,
        [
            ("student1", "D"),
            ("student2", "D"),
            ("student3", "D"),
            ("student4", "D"),
            ("student5", "A"),
        ],
    )
    client.post(f"/api/v1/session/{sid}/close", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher_headers)
    r8 = client.get(f"/api/v1/session/{sid}/speech?lang=quc", headers=teacher_headers)
    assert r8.status_code == 200 and r8.content == FAKE_WAV

    # --- Round 9: First-Press Lock test (student votes twice -> 409 conflict on duplicate) ---
    client.post(f"/api/v1/session/{sid}/next", headers=teacher_headers)
    v1 = client.post(
        f"/api/v1/session/{sid}/vote",
        json={"selected_option": "B"},
        headers=auth_headers(client, "student1"),
    )
    assert v1.status_code == 200
    v2 = client.post(
        f"/api/v1/session/{sid}/vote",
        json={"selected_option": "C"},
        headers=auth_headers(client, "student1"),
    )
    assert v2.status_code == 409  # Locked on first press!
    _cast_votes(
        client, sid, [("student2", "B"), ("student3", "B")]
    )  # total 3 votes: all B (100%)
    client.post(f"/api/v1/session/{sid}/close", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher_headers)
    r9 = client.get(f"/api/v1/session/{sid}/speech?lang=es", headers=teacher_headers)
    assert r9.status_code == 200

    # --- Round 10: 4/5 = 80% Distractor C (>51%) -> SPEAKS Spanish ---
    client.post(f"/api/v1/session/{sid}/next", headers=teacher_headers)
    _cast_votes(
        client,
        sid,
        [
            ("student1", "C"),
            ("student2", "C"),
            ("student3", "C"),
            ("student4", "C"),
            ("student5", "A"),
        ],
    )
    client.post(f"/api/v1/session/{sid}/close", headers=teacher_headers)
    client.post(f"/api/v1/session/{sid}/reveal", headers=teacher_headers)
    r10 = client.get(f"/api/v1/session/{sid}/speech?lang=es", headers=teacher_headers)
    assert r10.status_code == 200 and r10.content == FAKE_WAV
