"""Shared helpers for the fleet tests: 15 simulated ESP32 clickers and 15 phones.

Clickers go through the real staff and device endpoints; phones log in normally.
Seeding writes students and questions straight to the database. The only direct reads
are the stored vote rows, for the student and transport label of each vote.
"""

import sqlite3
import threading
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from fastapi.testclient import TestClient

from core.db.question_repository import create_question
from modes.quiz.contracts.models import DistractorDetail, QuizQuestionCreate
from tests.conftest import PRE_HASHED_PIN_1234, auth_headers

FLEET_SIZE = 15
TEACHER_USERNAME = "teacher1"
CLICKER_USERNAME_PREFIX = "fleet_clicker"
PHONE_USERNAME_PREFIX = "fleet_phone"
# Clicker number 1 gets ESP32-0000A1, the first id in the real format.
CLICKER_DEVICE_ID_OFFSET = 0xA0
DEVICE_AUTH_URL = "/api/v1/devices/auth"
OPTIONS = ("A", "B", "C", "D")
CORRECT_OPTION = "A"
DISTRACTOR_OPTION = "B"
QUESTION_DISTRACTORS = {
    "B": DistractorDetail(misconception="plus_one", explanation="Sumaste 1 de mas."),
    "C": DistractorDetail(misconception="minus_one", explanation="Sumaste 1 de menos."),
    "D": DistractorDetail(misconception="subtracted", explanation="Restaste."),
}
# The longest duration the API allows, so no round can expire mid-test.
MATCH_DURATION_SECONDS = 300
# A start line that never opens fails the test instead of hanging it.
START_LINE_TIMEOUT_SECONDS = 30

Ballot = tuple[dict[str, str], str]


@dataclass(frozen=True)
class StudentAccount:
    student_id: int
    username: str


@dataclass(frozen=True)
class Clicker:
    student_id: int
    device_id: str
    # Shown once by the teacher; kept so the clicker can authenticate again.
    secret: str
    # Bearer headers of the session its latest authentication issued.
    headers: dict[str, str]


@dataclass(frozen=True)
class Phone:
    student_id: int
    headers: dict[str, str]


Voter = Clicker | Phone


@dataclass(frozen=True)
class Arena:
    teacher_headers: dict[str, str]
    clickers: list[Clicker]
    phones: list[Phone]


def seed_students(
    conn: sqlite3.Connection, username_prefix: str, count: int
) -> list[StudentAccount]:
    """Inserts students named <prefix>_01 .. <prefix>_NN with the default test PIN."""
    accounts: list[StudentAccount] = []
    for number in range(1, count + 1):
        username = f"{username_prefix}_{number:02d}"
        cursor = conn.execute(
            "INSERT INTO users (username, hashed_pin, role) VALUES (?, ?, 'student')",
            (username, PRE_HASHED_PIN_1234),
        )
        accounts.append(StudentAccount(student_id=cursor.lastrowid, username=username))
    conn.commit()
    return accounts


def seed_questions(conn: sqlite3.Connection, count: int) -> list[str]:
    """Creates questions whose A is correct; B, C and D are diagnosed distractors."""
    question_ids = [
        create_question(
            conn,
            QuizQuestionCreate(
                topic="arithmetic",
                subconcept="addition",
                question_text=f"Fleet question {number}: 2 + 3?",
                options={"A": "5", "B": "6", "C": "4", "D": "1"},
                correct_option=CORRECT_OPTION,
                distractors=QUESTION_DISTRACTORS,
            ),
        )
        for number in range(1, count + 1)
    ]
    conn.commit()
    return question_ids


def clicker_device_id(clicker_number: int) -> str:
    """A clicker id in the real format: 'ESP32-' and six uppercase hex digits."""
    return f"ESP32-{CLICKER_DEVICE_ID_OFFSET + clicker_number:06X}"


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def assign_device(
    client: TestClient, teacher_headers: dict[str, str], device_id: str, user_id: int
):
    return client.post(
        f"/api/v1/staff/devices/{device_id}/assign",
        json={"user_id": user_id},
        headers=teacher_headers,
    )


def unassign_device(
    client: TestClient, teacher_headers: dict[str, str], device_id: str
):
    return client.post(
        f"/api/v1/staff/devices/{device_id}/unassign", headers=teacher_headers
    )


def authenticate_clicker(client: TestClient, device_id: str, secret: str):
    """The clicker's own login: its device id and secret in, a session out."""
    return client.post(DEVICE_AUTH_URL, json={"device_id": device_id, "secret": secret})


def provision_clicker(
    client: TestClient,
    teacher_headers: dict[str, str],
    student: StudentAccount,
    device_id: str,
) -> Clicker:
    """Registers, assigns and issues a secret to a clicker, then logs it in."""
    registered = client.post(
        "/api/v1/staff/devices", json={"device_id": device_id}, headers=teacher_headers
    )
    assert registered.status_code == 201, registered.text
    assigned = assign_device(client, teacher_headers, device_id, student.student_id)
    assert assigned.status_code == 200, assigned.text
    issued = client.post(
        f"/api/v1/staff/devices/{device_id}/secret", headers=teacher_headers
    )
    assert issued.status_code == 200, issued.text
    secret = issued.json()["secret"]
    authenticated = authenticate_clicker(client, device_id, secret)
    assert authenticated.status_code == 200, authenticated.text
    return Clicker(
        student_id=student.student_id,
        device_id=device_id,
        secret=secret,
        headers=bearer(authenticated.json()["session_id"]),
    )


def provision_fleet(
    client: TestClient, teacher_headers: dict[str, str], students: list[StudentAccount]
) -> list[Clicker]:
    """One clicker per student, numbered from 1 in roster order."""
    return [
        provision_clicker(client, teacher_headers, student, clicker_device_id(number))
        for number, student in enumerate(students, start=1)
    ]


def set_up_arena(client: TestClient, conn: sqlite3.Connection) -> Arena:
    """The teacher, 15 provisioned clickers and 15 logged-in phones."""
    teacher_headers = auth_headers(client, TEACHER_USERNAME)
    clickers = provision_fleet(
        client,
        teacher_headers,
        seed_students(conn, CLICKER_USERNAME_PREFIX, FLEET_SIZE),
    )
    phones = [
        Phone(
            student_id=student.student_id,
            headers=auth_headers(client, student.username),
        )
        for student in seed_students(conn, PHONE_USERNAME_PREFIX, FLEET_SIZE)
    ]
    return Arena(teacher_headers=teacher_headers, clickers=clickers, phones=phones)


def start_match(
    client: TestClient,
    conn: sqlite3.Connection,
    teacher_headers: dict[str, str],
    question_count: int,
) -> str:
    """Seeds questions, creates a match on them as the teacher and starts it."""
    question_ids = seed_questions(conn, question_count)
    created = client.post(
        "/api/v1/session",
        json={
            "title": "Fleet match",
            "topic": "arithmetic",
            "question_ids": question_ids,
            "duration_seconds": MATCH_DURATION_SECONDS,
        },
        headers=teacher_headers,
    )
    assert created.status_code == 201, created.text
    session_id = created.json()["id"]
    started = client.post(
        f"/api/v1/session/{session_id}/start", headers=teacher_headers
    )
    assert started.status_code == 200, started.text
    return session_id


def cast_vote(
    client: TestClient, session_id: str, headers: dict[str, str], option: str
):
    return client.post(
        f"/api/v1/session/{session_id}/vote",
        json={"selected_option": option},
        headers=headers,
    )


def submit_votes_concurrently(
    client: TestClient, session_id: str, ballots: Sequence[Ballot]
) -> list[int]:
    """Sends every ballot from its own thread, all released at the same moment.

    Returns the status codes in ballot order.
    """
    all_clients_ready = threading.Barrier(len(ballots))

    def _send(ballot: Ballot) -> int:
        headers, option = ballot
        all_clients_ready.wait(timeout=START_LINE_TIMEOUT_SECONDS)
        return cast_vote(client, session_id, headers, option).status_code

    with ThreadPoolExecutor(max_workers=len(ballots)) as executor:
        return list(executor.map(_send, ballots))


def ballots_for(voters: Sequence[Voter], option: str) -> list[Ballot]:
    return [(voter.headers, option) for voter in voters]


def interleave(first: Sequence[Voter], second: Sequence[Voter]) -> list[Voter]:
    """[first[0], second[0], first[1], second[1], ...] for two equally long lists."""
    assert len(first) == len(second)
    return [voter for pair in zip(first, second) for voter in pair]


def votes_cast_in_current_round(client: TestClient, session_id: str) -> int:
    state = client.get(f"/api/v1/session/{session_id}")
    assert state.status_code == 200, state.text
    return state.json()["current_round"]["votes_cast"]


def reveal_current_round(
    client: TestClient, session_id: str, teacher_headers: dict[str, str]
) -> dict[str, Any]:
    revealed = client.post(
        f"/api/v1/session/{session_id}/reveal", headers=teacher_headers
    )
    assert revealed.status_code == 200, revealed.text
    return revealed.json()


def advance_to_next_round(
    client: TestClient, session_id: str, teacher_headers: dict[str, str]
) -> None:
    advanced = client.post(
        f"/api/v1/session/{session_id}/next", headers=teacher_headers
    )
    assert advanced.status_code == 200, advanced.text


def stored_votes(conn: sqlite3.Connection, session_id: str) -> list[sqlite3.Row]:
    """Every stored vote of a match, with the transport label the server gave it."""
    return conn.execute(
        "SELECT round_id, student_id, transport_type, device_id "
        "FROM quiz_session_votes WHERE session_id = ? "
        "ORDER BY student_id, round_id",
        (session_id,),
    ).fetchall()
