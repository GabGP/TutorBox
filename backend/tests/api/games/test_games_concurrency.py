"""Week 6 acceptance under load: reconnecting phones resend their queues, 100% of events stored, 0 duplicates."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

EVENTS = "/api/v1/games/events"


def _scalar(conn: sqlite3.Connection, query: str) -> int:
    return conn.execute(query).fetchone()[0]


def make_event(client_event_id: str) -> dict:
    return {
        "client_event_id": client_event_id,
        "grade": "primero",
        "lesson_id": "sumar-jocotes",
        "round_index": 0,
        "attempt": 1,
        "is_correct": True,
        "answer": "5",
        "expected": "5",
        "occurred_at": "2026-10-09T15:04:05Z",
        "app_version": "1",
    }


def test_eight_phones_resending_the_same_queue_store_each_event_once(
    temp_db, client: TestClient
):
    _, conn = temp_db
    queue = {
        "install_id": "install-shared-000001",
        "events": [make_event(f"evt-queue00-{index:06d}") for index in range(1, 26)],
    }

    def _resend_queue(_: int):
        return client.post(EVENTS, json=queue)

    with ThreadPoolExecutor(max_workers=8) as executor:
        responses = list(executor.map(_resend_queue, range(8)))

    assert [response.status_code for response in responses] == [200] * 8
    assert sum(response.json()["accepted"] for response in responses) == 25
    assert sum(response.json()["duplicates"] for response in responses) == 175
    assert _scalar(conn, "SELECT COUNT(*) FROM game_events") == 25
    assert (
        _scalar(conn, "SELECT COUNT(DISTINCT client_event_id) FROM game_events") == 25
    )


def test_ten_phones_with_different_queues_lose_no_event(temp_db, client: TestClient):
    _, conn = temp_db

    def _post_own_queue(phone: int):
        queue = {
            "install_id": f"install-phone{phone:02d}-000001",
            "events": [
                make_event(f"evt-phone{phone:02d}-{index:06d}")
                for index in range(1, 21)
            ],
        }
        return client.post(EVENTS, json=queue)

    with ThreadPoolExecutor(max_workers=10) as executor:
        responses = list(executor.map(_post_own_queue, range(10)))

    assert [response.status_code for response in responses] == [200] * 10
    assert [response.json()["accepted"] for response in responses] == [20] * 10
    assert _scalar(conn, "SELECT COUNT(*) FROM game_events") == 200
    assert _scalar(conn, "SELECT COUNT(DISTINCT install_id) FROM game_events") == 10
