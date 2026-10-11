"""Shared helpers for the hardware clicker transport tests (api/clicker)."""

import sqlite3

from fastapi.testclient import TestClient

from core.db.question_repository import create_question
from modes.quiz.contracts.models import DistractorDetail, QuizQuestionCreate

CLICKER_ID = "ESP32-A4CF12"
SECRET = "0123456789abcdef0123456789abcdef"
OTHER_SECRET = "fedcba9876543210fedcba9876543210"


def clicker_headers(device_id: str = CLICKER_ID, secret: str = SECRET) -> dict:
    return {"X-Clicker-Id": device_id, "X-Clicker-Secret": secret}


def checkin(
    client: TestClient,
    device_id: str = CLICKER_ID,
    secret: str = SECRET,
    **vitals,
):
    return client.post(
        "/api/v1/clicker/checkin",
        json=vitals,
        headers=clicker_headers(device_id, secret),
    )


def clicker_vote(
    client: TestClient,
    round_id: str,
    option: str = "B",
    device_id: str = CLICKER_ID,
    secret: str = SECRET,
    **extra,
):
    return client.post(
        "/api/v1/clicker/vote",
        json={"round_id": round_id, "selected_option": option, **extra},
        headers=clicker_headers(device_id, secret),
    )


def assign(client: TestClient, headers: dict, device_id: str, user_id: int) -> None:
    response = client.post(
        f"/api/v1/staff/devices/{device_id}/assign",
        json={"user_id": user_id},
        headers=headers,
    )
    assert response.status_code == 200, response.json()


def seed_questions(conn: sqlite3.Connection, count: int = 2) -> list[str]:
    ids = [
        create_question(
            conn,
            QuizQuestionCreate(
                topic="arithmetic",
                subconcept="addition",
                question_text=f"{index} + 1?",
                options={"A": "x", "B": "y", "C": "z", "D": "w"},
                correct_option="A",
                distractors={
                    key: DistractorDetail(misconception=slug, explanation="Revisa.")
                    for key, slug in (
                        ("B", "plus_one"),
                        ("C", "minus_one"),
                        ("D", "subtracted"),
                    )
                },
            ),
        )
        for index in range(count)
    ]
    conn.commit()
    return ids


def start_match(client: TestClient, headers: dict, question_ids: list[str]) -> str:
    """Creates and starts a match; returns the session id (round 0 is open)."""
    created = client.post(
        "/api/v1/session",
        json={"title": "Clickers", "topic": "arithmetic", "question_ids": question_ids},
        headers=headers,
    )
    assert created.status_code == 201, created.json()
    session_id = created.json()["id"]
    started = client.post(f"/api/v1/session/{session_id}/start", headers=headers)
    assert started.status_code == 200, started.json()
    return session_id
