"""End-to-end test: the real clicker firmware, run on a PC, against a real Utz'tutor.

Starts the backend (uvicorn, throwaway database), starts the simulated clicker
(build_sim.sh), then plays a classroom: the clicker makes its own secret and enrolls
itself, the teacher assigns it, questions open, buttons are pressed, Wi-Fi and the
server drop out, the teacher unassigns and deletes it, and the reset gesture (A and D
held at power-on) makes it forget its secret.

    python firmware/clicker/hosttest/e2e_test.py   (Linux, macOS or WSL)

Needs the backend's Python environment (pip install -e "backend[dev]") and g++.
"""

import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from e2e_backend import Api, Backend, enrollments, free_port, stored_digest, votes
from e2e_clicker import HERE, SIM, Clicker, stored_secret

DEVICE = "ESP32-A4CF12"
SECRET_SHAPE = re.compile(r"^[0-9a-f]{32}$")
# The box keeps the SHA-256 of a secret (64 hex characters), never the secret.
DIGEST_SHAPE = re.compile(r"^[0-9a-f]{64}$")
TOKEN_SHAPE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)


def step(text: str) -> None:
    print(f"  - {text}", flush=True)


def wait_for(check, seconds: float = 5.0):
    """Returns check()'s first truthy result, or fails after `seconds`."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        result = check()
        if result:
            return result
        time.sleep(0.2)
    raise AssertionError(f"still false after {seconds} s: {check.__name__}")


def main() -> int:
    if not SIM.exists():
        subprocess.run(["bash", str(HERE / "build_sim.sh")], check=True)
    work = Path(tempfile.mkdtemp(prefix="clicker-e2e-"))
    db_path, nvs = str(work / "utztutor.db"), str(work / "nvs.txt")
    port = free_port()
    backend, api = Backend(db_path, port), Api(port)
    clickers: list[Clicker] = []
    secrets: list[str] = []  # every secret the clicker has stored: none may be printed

    def remember_secret() -> None:
        secret = stored_secret(nvs)
        if secret and secret not in secrets:
            secrets.append(secret)

    def power_on(held: str = "") -> Clicker:
        remember_secret()  # the secret the clicker switched off just now holds
        clickers.append(Clicker(port, nvs, held))
        return clickers[-1]

    def online_in_lobby():
        seen = api.clicker_in_lobby("ana")
        return seen if seen and seen["status"] == "online" else None

    try:
        print("Utz'tutor clicker end-to-end test")
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

        step("1. power on, empty flash: it makes a secret and enrolls itself")
        clicker = power_on()
        clicker.expect(rf"Device id : {DEVICE}")
        clicker.expect("first boot: created this clicker's secret")
        clicker.expect("Wi-Fi connected")
        clicker.expect(
            rf"Connected, but not assigned\. Assign {DEVICE} to a student "
            r"in Clickers on /maestro/"
        )
        clicker.expect("LED Magenta")
        # Nobody called the staff API for it: the box made the row at its first login.
        secret_first = stored_secret(nvs)
        assert secret_first and SECRET_SHAPE.match(secret_first), secret_first
        row = api.device(DEVICE)
        assert row is not None and row["assigned_user_id"] is None, row
        assert row["secret_issued_at"], row
        assert enrollments(db_path) == ["device_enrolled"], enrollments(db_path)
        assert DEVICE in api.call("GET", "/presence/class")["unassigned_clickers"]
        clicker.send("press A")
        clicker.expect("Button A ignored: this clicker needs the teacher")
        digest_first = stored_digest(db_path, DEVICE)
        assert digest_first and DIGEST_SHAPE.match(digest_first), digest_first
        assert digest_first != secret_first

        step("2. the teacher assigns it to ana: ready within 5 s, online in the lobby")
        api.call("POST", f"/staff/devices/{DEVICE}/assign", {"user_id": ana_id})
        clicker.expect("Assigned to ana: ready to vote")
        clicker.expect("LED Green")

        seen = wait_for(online_in_lobby)
        assert seen["device_id"] == DEVICE and seen["rssi"] == -58, seen
        assert seen["battery_pct"] is None, seen  # the sense resistors are optional

        step("3a. question 1 opens: white; B is counted as a hardware vote")
        session = api.call(
            "POST",
            "/session/",
            {"title": "E2E", "topic": "arithmetic", "question_ids": question_ids},
            expect=201,
        )
        sid = session["id"]
        clicker.quiet("Question open", 1.5)  # the lobby: nothing to answer yet
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

        step("3b. second press in the same question: refused locally, red")
        clicker.send("press C")
        clicker.expect("Button C ignored: this question is already answered")
        clicker.expect("LED Red")

        step("3c. question 2: a very short tap (seen only by the interrupt) counts")
        for action in ("close", "reveal", "next"):
            api.call("POST", f"/session/{sid}/{action}")
        clicker.expect(rf"Question open \({sid}_r1\)")
        clicker.send("tap D")
        clicker.expect("Vote D counted")

        step("3d. Wi-Fi drops and comes back: same session, no new login")
        clicker.send("wifi off")
        clicker.expect("Wi-Fi lost")
        clicker.expect("LED Blue")
        clicker.send("press A")
        clicker.expect("Button A ignored: not connected yet")
        clicker.send("wifi on")
        clicker.expect("Wi-Fi connected again")
        clicker.quiet("Logging in", 1.5)

        step("3e. Utz'tutor goes down: blue slow blink; back up: recovers by itself")
        backend.stop()
        for _ in range(3):
            clicker.expect(r"Utz'tutor did not answer \(-1\)")
        clicker.expect(r"status: server-unreachable", timeout=20)
        backend.start()
        clicker.expect("Utz'tutor answers again", timeout=10)

        step("3f. question 3 after the outage: A counted")
        for action in ("close", "reveal", "next"):
            api.call("POST", f"/session/{sid}/{action}")
        clicker.expect(rf"Question open \({sid}_r2\)")
        clicker.send("press A")
        clicker.expect("Vote A counted")
        assert [v[1] for v in votes(db_path)] == ["B", "D", "A"]
        assert {v[2] for v in votes(db_path)} == {"hardware"}

        step("4. unassign, then assign again: it notices within 5 s and is ready again")
        api.call("POST", f"/staff/devices/{DEVICE}/unassign")
        clicker.expect("Utz'tutor ended this clicker's session")
        clicker.expect(rf"Connected, but not assigned\. Assign {DEVICE}")
        clicker.send("press A")
        clicker.expect("Button A ignored: this clicker needs the teacher")
        api.call("POST", f"/staff/devices/{DEVICE}/assign", {"user_id": ana_id})
        clicker.expect("Assigned to ana: ready to vote")

        step("5. power cycle: the same secret is in flash, it logs in as ana by itself")
        secret_before = stored_secret(nvs)
        assert secret_before and SECRET_SHAPE.match(secret_before), secret_before
        clicker.stop()
        clicker = power_on()
        clicker.expect("secret found in flash")
        clicker.expect("Assigned to ana: ready to vote")
        assert stored_secret(nvs) == secret_before
        assert stored_digest(db_path, DEVICE) == digest_first
        assert not any("first boot" in line for line in clicker.printed)

        step("6. the teacher deletes it while it runs: its next login enrolls it again")
        api.call("DELETE", f"/staff/devices/{DEVICE}")
        clicker.expect("Utz'tutor ended this clicker's session")
        clicker.expect(rf"Connected, but not assigned\. Assign {DEVICE}")
        assert not any("refused" in line for line in clicker.printed)
        # Same secret, same digest
        assert stored_digest(db_path, DEVICE) == digest_first
        assert api.device(DEVICE)["assigned_user_id"] is None

        step("7a. reset: A and D held; the box still has the old secret: refused")
        clicker.stop()
        clicker = power_on(held="AD")
        clicker.expect("LED Magenta")  # held: the light shows the hold
        clicker.expect("LED White", timeout=12)  # 5 s held, then white for 1 s
        clicker.expect("reset: this clicker will make a new secret")
        clicker.expect("first boot: created this clicker's secret")
        clicker.expect(r"Utz'tutor refused this clicker's secret \(HTTP 401")
        clicker.expect(rf"Fix: delete {DEVICE} in Clickers on /maestro/")
        secret_reset = stored_secret(nvs)
        assert secret_reset and SECRET_SHAPE.match(secret_reset), secret_reset
        assert secret_reset != secret_before
        # The box still has the old one
        assert stored_digest(db_path, DEVICE) == digest_first
        clicker.quiet("Logging in|Login failed|locked", 4)  # refused: no timer

        step("7b. the teacher deletes the row, a press: it enrolls the new secret")
        api.call("DELETE", f"/staff/devices/{DEVICE}")
        clicker.send("press B")
        clicker.expect("Button B: asking the Utz'tutor again")
        clicker.expect(rf"Connected, but not assigned\. Assign {DEVICE}")
        digest_reset = stored_digest(db_path, DEVICE)
        assert digest_reset and digest_reset != digest_first
        api.call("POST", f"/staff/devices/{DEVICE}/assign", {"user_id": ana_id})
        clicker.expect("Assigned to ana: ready to vote")

        step("8a. a hold let go early: nothing is reset, it logs in as ana")
        digest_before_8 = stored_digest(db_path, DEVICE)
        secret_before_8 = stored_secret(nvs)
        clicker.stop()
        clicker = power_on(held="AD")
        clicker.expect("LED Magenta")  # the hold has begun
        clicker.send("release A")
        clicker.expect("secret found in flash")
        clicker.expect("Assigned to ana: ready to vote")
        assert stored_digest(db_path, DEVICE) == digest_before_8
        assert stored_secret(nvs) == secret_before_8
        assert not any("reset:" in line for line in clicker.printed)

        step("8b. one button held alone: nothing is reset, it logs in as ana")
        clicker.stop()
        clicker = power_on(held="A")
        clicker.expect("secret found in flash")
        clicker.expect("Assigned to ana: ready to vote")
        assert stored_digest(db_path, DEVICE) == digest_before_8
        assert stored_secret(nvs) == secret_before_8
        assert not any("reset:" in line for line in clicker.printed)

        step("9. nothing the clickers printed carries a secret or a token")
        remember_secret()
        time.sleep(0.5)
        # The first secret, and the one made after the reset.
        assert len(set(secrets)) == 2, secrets
        for line in (line for c in clickers for line in c.printed):
            assert not any(secret in line for secret in secrets), line
            assert not TOKEN_SHAPE.search(line), line

        step("10. no reply was read in a way that freezes the real HTTPClient")
        # The heartbeat's 204 has no length: reading its body on the kept-open
        # connection waits for nginx to close it, about a minute (sim/sim_http.cpp).
        for line in (line for c in clickers for line in c.printed):
            assert "HTTPClient trap" not in line, line

        print("PASS: all clicker end-to-end steps")
        return 0
    finally:
        for clicker in clickers:
            clicker.stop()
        if clickers and os.environ.get("E2E_VERBOSE"):
            print("\n--- last clicker's serial log ---")
            print("\n".join(clickers[-1].transcript))
        backend.stop()


if __name__ == "__main__":
    sys.exit(main())
