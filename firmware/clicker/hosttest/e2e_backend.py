"""The Utz'tutor side of the end-to-end test: the backend process, its API as the
teacher uses it, and what its database holds afterwards."""

import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Backend:
    def __init__(self, db_path: str, port: int):
        self.db_path, self.port, self.proc = db_path, port, None

    def start(self) -> None:
        env = dict(
            os.environ,
            DATABASE_PATH=self.db_path,
            PWA_STATIC_DIR="pwa/pilas",
            BCRYPT_ROUNDS="4",
            SEED_TEACHER_USERNAME="teacher1",
            SEED_TEACHER_PIN="1234",
        )
        # The command of the appliance's own unit (infra/systemd): main:app from src.
        command = [sys.executable, "-m", "uvicorn", "main:app"]
        command += [
            "--app-dir",
            str(REPO / "backend" / "src"),
            "--port",
            str(self.port),
        ]
        self.proc = subprocess.Popen(
            command,
            cwd=REPO / "backend",
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 30
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(
                    "backend exited at startup: run this script with the backend's "
                    'Python (pip install -e "backend[dev]")'
                )
            try:
                urllib.request.urlopen(
                    f"http://127.0.0.1:{self.port}/health", timeout=1
                )
                return
            except OSError:
                time.sleep(0.2)
        raise RuntimeError("backend did not answer /health within 30 s")

    def stop(self) -> None:
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=10)
            self.proc = None


class Api:
    def __init__(self, port: int):
        self.base = f"http://127.0.0.1:{port}/api/v1"
        self.token = None

    def call(self, method: str, path: str, body=None, expect=200):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method)
        request.add_header("Content-Type", "application/json")
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                status, payload = response.status, response.read()
        except urllib.error.HTTPError as err:
            status, payload = err.code, err.read()
        assert status == expect, f"{method} {path}: {status} {payload!r}"
        return json.loads(payload) if payload else None

    def login(self) -> None:
        self.token = self.call(
            "POST", "/auth/login", {"username": "teacher1", "pin": "1234"}
        )["session_id"]

    def device(self, device_id: str) -> dict | None:
        """The clicker's row in the teacher's fleet list, or None."""
        for row in self.call("GET", "/staff/devices")["devices"]:
            if row["device_id"] == device_id:
                return row
        return None

    def clicker_in_lobby(self, username: str) -> dict | None:
        """The clicker of `username` as the teacher's lobby lists it."""
        view = self.call("GET", "/presence/class")
        for student in view["students"]:
            if student["username"] == username:
                return student["clicker"]
        return None


def stored_digest(db_path: str, device_id: str) -> str | None:
    """The digest of a clicker's secret on the Utz'tutor, or None if it has no row."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT secret_hash FROM devices WHERE device_id = ?", (device_id,)
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def votes(db_path: str) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            "SELECT round_id, selected_option, transport_type, device_id, student_id "
            "FROM quiz_session_votes ORDER BY created_at, rowid"
        ).fetchall()
    finally:
        conn.close()


def enrollments(db_path: str) -> list[str]:
    """The audit actions about the clicker fleet, in the order they were written."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT action FROM audit_logs WHERE action LIKE 'device_%' ORDER BY id"
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()
