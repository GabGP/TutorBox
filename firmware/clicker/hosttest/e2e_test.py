"""End-to-end test: the real clicker firmware, run on a PC, against a real TutorBox.

Starts the backend (uvicorn, throwaway database), starts the simulated clicker
(build_sim.sh), then plays a classroom: enroll, teacher assigns, questions open,
buttons pressed, Wi-Fi and server drop out, the clicker's flash is wiped.

    python firmware/clicker/hosttest/e2e_test.py   (Linux, macOS or WSL)

Needs the backend's Python environment (pip install -e "backend[dev]") and g++.
"""

import json
import os
import queue
import re
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SIM = HERE / "build" / "clicker_sim"
DEVICE = "ESP32-A4CF12"


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
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.main:app", "--port", str(self.port)],
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


class Clicker:
    """The simulated clicker process, with a reader thread and expect()."""

    def __init__(self, port: int, nvs: str):
        env = dict(
            os.environ, CLICKER_SIM_SERVER=f"127.0.0.1:{port}", CLICKER_SIM_NVS=nvs
        )
        self.proc = subprocess.Popen(
            [str(SIM)],
            cwd=HERE,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str] = queue.Queue()
        self.transcript: list[str] = []
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\n"))

    def send(self, command: str) -> None:
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def expect(self, pattern: str, timeout: float = 8.0) -> re.Match:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = self.lines.get(timeout=0.1)
            except queue.Empty:
                continue
            self.transcript.append(line)
            match = re.search(pattern, line)
            if match:
                return match
        tail = "\n    ".join(self.transcript[-25:])
        raise AssertionError(
            f"timed out waiting for /{pattern}/; last lines:\n    {tail}"
        )

    def quiet(self, pattern: str, seconds: float) -> None:
        """Asserts that no line matches `pattern` for `seconds`."""
        deadline = time.time() + seconds
        while time.time() < deadline:
            try:
                line = self.lines.get(timeout=0.1)
            except queue.Empty:
                continue
            self.transcript.append(line)
            assert not re.search(pattern, line), f"unexpected line: {line}"

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.send("quit")
            self.proc.wait(timeout=5)


def step(text: str) -> None:
    print(f"  - {text}", flush=True)


def votes(db_path: str) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            "SELECT round_id, selected_option, transport_type, device_id, student_id "
            "FROM quiz_session_votes ORDER BY created_at, rowid"
        ).fetchall()
    finally:
        conn.close()


def main() -> int:
    if not SIM.exists():
        subprocess.run(["bash", str(HERE / "build_sim.sh")], check=True)
    work = Path(tempfile.mkdtemp(prefix="clicker-e2e-"))
    db_path, nvs = str(work / "tutorbox.db"), str(work / "nvs.txt")
    port = free_port()
    backend, api = Backend(db_path, port), Api(port)
    clicker = None
    try:
        print("TutorBox clicker end-to-end test")
        backend.start()
        api.login()
        student = api.call(
            "POST", "/staff/users", {"username": "ana", "pin": "4321"}, expect=201
        )
        assert student["username"] == "ana"
        ana_id = next(
            u["id"]
            for u in api.call("GET", "/staff/users")["users"]
            if u["username"] == "ana"
        )
        bank = api.call("GET", "/quiz/questions?topic=arithmetic&limit=3")["questions"]
        question_ids = [q["id"] for q in bank]
        assert len(question_ids) == 3

        step(
            "power on: joins Wi-Fi, creates its secret, enrolls, waits for the teacher"
        )
        clicker = Clicker(port, nvs)
        clicker.expect(rf"Device id : {DEVICE}")
        clicker.expect("tx power 34")
        clicker.expect("first boot: created this clicker's secret")
        clicker.expect("Wi-Fi connected")
        clicker.expect(f"Waiting for the teacher to assign {DEVICE}")
        clicker.expect("LED Magenta")
        clicker.send("press A")
        clicker.expect("Button A ignored: this clicker needs the teacher")
        roster = {
            d["device_id"]: d for d in api.call("GET", "/staff/devices")["devices"]
        }
        assert roster[DEVICE]["enrolled"] and roster[DEVICE]["online"], roster
        assert roster[DEVICE]["firmware"] == "1.0.0" and roster[DEVICE]["rssi"] == -58

        step("teacher assigns it to ana: ready, green blip")
        api.call("POST", f"/staff/devices/{DEVICE}/assign", {"user_id": ana_id})
        clicker.expect("Assigned to a student: ready to vote")
        clicker.expect("LED Green")

        step("question 1 opens: white; B is counted as a hardware vote")
        session = api.call(
            "POST",
            "/session/",
            {"title": "E2E", "topic": "arithmetic", "question_ids": question_ids},
            expect=201,
        )
        sid = session["id"]
        api.call("POST", f"/session/{sid}/start")
        clicker.expect(rf"Question open \({sid}_r0\)")
        clicker.expect("LED White")
        clicker.send("press B")
        clicker.expect("Button B: sending vote")
        clicker.expect("Vote B counted")
        clicker.expect("LED Green")
        state = api.call("GET", f"/session/{sid}")
        assert state["current_round"]["votes_cast"] == 1, state
        assert votes(db_path) == [(f"{sid}_r0", "B", "hardware", DEVICE, ana_id)]

        step("second press in the same question: refused locally, red")
        clicker.send("press C")
        clicker.expect("Button C ignored: this question is already answered")
        clicker.expect("LED Red")

        step("question 2: a very short tap (seen only by the interrupt) still counts")
        for action in ("close", "reveal", "next"):
            api.call("POST", f"/session/{sid}/{action}")
        clicker.expect(rf"Question open \({sid}_r1\)")
        clicker.send("tap D")
        clicker.expect("Vote D counted")

        step("Wi-Fi drops and comes back")
        clicker.send("wifi off")
        clicker.expect("Wi-Fi lost")
        clicker.expect("LED Blue")
        clicker.send("press A")
        clicker.expect("Button A ignored: not connected yet")
        clicker.send("wifi on")
        clicker.expect("Wi-Fi connected")
        clicker.expect("Assigned to a student: ready to vote")

        step("TutorBox goes down: blue slow blink; back up: recovers by itself")
        backend.stop()
        for _ in range(3):
            clicker.expect(r"Check-in failed \(-1")
        clicker.expect(r"status: server-unreachable", timeout=20)
        backend.start()
        clicker.expect("Assigned to a student: ready to vote", timeout=10)

        step("question 3 after the outage: A counted")
        for action in ("close", "reveal", "next"):
            api.call("POST", f"/session/{sid}/{action}")
        clicker.expect(rf"Question open \({sid}_r2\)")
        clicker.send("press A")
        clicker.expect("Vote A counted")
        assert [v[1] for v in votes(db_path)] == ["B", "D", "A"]
        assert {v[2] for v in votes(db_path)} == {"hardware"}

        step("power cycle: same secret from flash, no re-enrollment")
        clicker.stop()
        clicker = Clicker(port, nvs)
        clicker.expect(rf"Device id : {DEVICE}")
        clicker.expect("Assigned to a student: ready to vote")
        assert not any("first boot" in line for line in clicker.transcript)

        step("flash wiped (new secret): refused, teacher removes it, re-enrolls")
        clicker.stop()
        os.remove(nvs)
        clicker = Clicker(port, nvs)
        clicker.expect("first boot: created this clicker's secret")
        clicker.expect(r"TutorBox refused this clicker \(HTTP 401")
        clicker.expect("LED Magenta")
        api.call("DELETE", f"/staff/devices/{DEVICE}")
        clicker.expect(f"Waiting for the teacher to assign {DEVICE}", timeout=10)

        print("PASS: all clicker end-to-end steps")
        return 0
    finally:
        if clicker:
            clicker.stop()
            if os.environ.get("E2E_VERBOSE"):
                print("\n--- last clicker's serial log ---")
                print("\n".join(clicker.transcript))
        backend.stop()


if __name__ == "__main__":
    sys.exit(main())
