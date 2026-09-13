"""Concurrency and burst load integration tests for real-time quiz voting.

Validates Week 3 acceptance criterion: 5-question match with 15 simultaneous
clients, zero lost votes, first-press lock race resolution, and concurrent polling.
"""

import sqlite3
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from core.db.question_repository import create_question
from modes.quiz.contracts.models import DistractorDetail, OptionKey, QuizQuestionCreate
from tests.conftest import PRE_HASHED_PIN_1234, auth_headers


def _seed_concurrency_roster(
    conn: sqlite3.Connection, student_count: int = 15
) -> list[str]:
    """Pre-seeds standard test accounts for concurrent student voters."""
    usernames = [
        f"concurrent_student_{index:02d}" for index in range(1, student_count + 1)
    ]
    records = [(name, PRE_HASHED_PIN_1234, "student") for name in usernames]
    conn.cursor().executemany(
        "INSERT INTO users (username, hashed_pin, role) VALUES (?, ?, ?)",
        records,
    )
    conn.commit()
    return usernames


def _create_test_question(
    conn: sqlite3.Connection,
    prompt_text: str,
    correct_key: OptionKey,
    options_map: dict[str, str],
    wrong_notes: dict[str, tuple[str, str]],
) -> str:
    """Helper creating a single diagnostic quiz question record."""
    distractors_data = {
        key: DistractorDetail(misconception=slug, explanation=note)
        for key, (slug, note) in wrong_notes.items()
    }
    return create_question(
        conn,
        QuizQuestionCreate(
            topic="arithmetic",
            subconcept="mixed_operations",
            question_text=prompt_text,
            options=options_map,
            correct_option=correct_key,
            distractors=distractors_data,
        ),
    )


def _seed_five_questions(conn: sqlite3.Connection) -> list[str]:
    """Creates a curated 5-question match suite."""
    questions: list[
        tuple[str, OptionKey, dict[str, str], dict[str, tuple[str, str]]]
    ] = [
        (
            "4 + 5?",
            "A",
            {"A": "9", "B": "8", "C": "10", "D": "1"},
            {
                "B": ("minus_one", "Menos uno."),
                "C": ("plus_one", "Mas uno."),
                "D": ("subtracted", "Restaste."),
            },
        ),
        (
            "6 * 7?",
            "B",
            {"A": "40", "B": "42", "C": "48", "D": "13"},
            {
                "A": ("table_error", "Desfase."),
                "C": ("off_by_two", "Desfase 2."),
                "D": ("added_numbers", "Sumaste."),
            },
        ),
        (
            "15 - 8?",
            "C",
            {"A": "6", "B": "8", "C": "7", "D": "23"},
            {
                "A": ("minus_one", "Menos uno."),
                "B": ("plus_one", "Mas uno."),
                "D": ("added_numbers", "Sumaste."),
            },
        ),
        (
            "20 / 4?",
            "D",
            {"A": "4", "B": "6", "C": "16", "D": "5"},
            {
                "A": ("table_error", "Error."),
                "B": ("off_by_one", "Mas uno."),
                "C": ("subtracted", "Restaste."),
            },
        ),
        (
            "9 + 7?",
            "A",
            {"A": "16", "B": "15", "C": "17", "D": "2"},
            {
                "B": ("minus_one", "Menos uno."),
                "C": ("plus_one", "Mas uno."),
                "D": ("subtracted", "Restaste."),
            },
        ),
    ]
    ids = [
        _create_test_question(conn, text, cor, opts, dist)
        for text, cor, opts, dist in questions
    ]
    conn.commit()
    return ids


def test_fifteen_concurrent_clients_five_question_match(staff_db, client: TestClient):
    """Simulates 15 simultaneous clients (web and hardware) across 5 rounds with 0 lost votes."""
    _, conn = staff_db
    question_ids = _seed_five_questions(conn)
    usernames = _seed_concurrency_roster(conn, student_count=15)
    teacher_token = auth_headers(client, "teacher1")
    student_tokens = [auth_headers(client, name) for name in usernames]

    create_payload = {
        "title": "Match Concurrente 15 Alumnos",
        "topic": "arithmetic",
        "question_ids": question_ids,
        "duration_seconds": 60,
    }
    create_response = client.post(
        "/api/v1/session", json=create_payload, headers=teacher_token
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    for round_index in range(5):
        if round_index == 0:
            client.post(f"/api/v1/session/{session_id}/start", headers=teacher_token)
        else:
            client.post(f"/api/v1/session/{session_id}/next", headers=teacher_token)

        state = client.get(f"/api/v1/session/{session_id}").json()
        assert state["current_round"]["status"] == "open"

        def _cast_client_vote(worker_index: int) -> int:
            token = student_tokens[worker_index]
            is_hardware = worker_index >= 10
            payload = {
                "selected_option": "A" if worker_index % 2 == 0 else "B",
                "transport_type": "hardware" if is_hardware else "web",
                "device_id": f"ESP32-DEVICE-{worker_index:02d}"
                if is_hardware
                else None,
                "response_time_ms": 500.0 + worker_index * 25.0,
            }
            response = client.post(
                f"/api/v1/session/{session_id}/vote", json=payload, headers=token
            )
            return response.status_code

        with ThreadPoolExecutor(max_workers=15) as executor:
            status_codes = list(executor.map(_cast_client_vote, range(15)))

        assert status_codes == [200] * 15, "Every concurrent student vote must succeed"

        round_state = client.get(f"/api/v1/session/{session_id}").json()[
            "current_round"
        ]
        assert round_state["votes_cast"] == 15, (
            f"Round {round_index} must record all 15 votes"
        )

        reveal_response = client.post(
            f"/api/v1/session/{session_id}/reveal", headers=teacher_token
        )
        assert reveal_response.status_code == 200
        assert reveal_response.json()["tally"]["total_votes"] == 15

    report = client.get(
        f"/api/v1/session/{session_id}/report", headers=teacher_token
    ).json()
    assert report["total_rounds"] == 5
    assert report["total_votes_cast"] == 75


def test_concurrent_first_press_lock_race_condition(staff_db, client: TestClient):
    """Verifies that simultaneous vote submissions for the same student cleanly resolve."""
    _, conn = staff_db
    question_ids = _seed_five_questions(conn)
    teacher_token = auth_headers(client, "teacher1")
    student_token = auth_headers(client, "student1")

    create_payload = {
        "title": "Race Test",
        "topic": "arithmetic",
        "question_ids": question_ids[:1],
        "duration_seconds": 30,
    }
    session_id = client.post(
        "/api/v1/session", json=create_payload, headers=teacher_token
    ).json()["id"]
    client.post(f"/api/v1/session/{session_id}/start", headers=teacher_token)

    options_to_attempt = ["A", "B", "C", "D", "A", "B", "C", "D"]

    def _submit_vote_attempt(option_choice: str) -> int:
        response = client.post(
            f"/api/v1/session/{session_id}/vote",
            json={"selected_option": option_choice, "transport_type": "web"},
            headers=student_token,
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(_submit_vote_attempt, options_to_attempt))

    assert results.count(200) == 1, "Exactly one concurrent vote must be accepted"
    assert results.count(409) == 7, (
        "All duplicate concurrent attempts must return 409 Conflict"
    )

    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM quiz_session_votes WHERE session_id = ?", (session_id,)
    )
    assert cursor.fetchone()[0] == 1


def test_concurrent_polling_during_active_voting_burst(staff_db, client: TestClient):
    """Ensures background client polling does not cause SQLite lock timeouts during voting."""
    _, conn = staff_db
    question_ids = _seed_five_questions(conn)
    usernames = _seed_concurrency_roster(conn, student_count=10)
    teacher_token = auth_headers(client, "teacher1")
    tokens = [auth_headers(client, name) for name in usernames]

    session_id = client.post(
        "/api/v1/session",
        json={
            "title": "Poll Load",
            "topic": "arithmetic",
            "question_ids": question_ids[:1],
        },
        headers=teacher_token,
    ).json()["id"]
    client.post(f"/api/v1/session/{session_id}/start", headers=teacher_token)

    def _voter_task(idx: int) -> int:
        res = client.post(
            f"/api/v1/session/{session_id}/vote",
            json={"selected_option": "C", "transport_type": "web"},
            headers=tokens[idx],
        )
        return res.status_code

    def _poller_task(_: int) -> int:
        res = client.get("/api/v1/session/current")
        return res.status_code

    with ThreadPoolExecutor(max_workers=16) as executor:
        vote_futures = [executor.submit(_voter_task, idx) for idx in range(10)]
        poll_futures = [executor.submit(_poller_task, idx) for idx in range(6)]
        vote_codes = [future.result() for future in vote_futures]
        poll_codes = [future.result() for future in poll_futures]

    assert vote_codes == [200] * 10
    assert poll_codes == [200] * 6
