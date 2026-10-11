"""Manage TutorBox hardware clickers from a laptop on the classroom Wi-Fi.

Standard library only: runs on Windows, macOS and Linux with any Python 3.10+.

    python tools/clickers/clickers.py list
    python tools/clickers/clickers.py assign ESP32-A4CF12 ana
    python tools/clickers/clickers.py assign-csv clase-3b.csv     (lines: device,username)
    python tools/clickers/clickers.py unassign ESP32-A4CF12
    python tools/clickers/clickers.py forget ESP32-A4CF12         (it re-enrolls by itself)
    python tools/clickers/clickers.py simulate 30 --auto-assign   (load test, no hardware)

Teacher login: --user (default teacher1) and the PIN from --pin, the TUTORBOX_PIN
environment variable, or a prompt. Server: --server or TUTORBOX_URL
(default http://192.168.8.2). Endpoints: docs/api/devices.md and docs/api/clicker.md.
"""

import argparse
import csv
import getpass
import json
import os
import random
import secrets
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request


class Api:
    def __init__(self, server: str):
        self.base = server.rstrip("/") + "/api/v1"
        self.token: str | None = None

    def call(self, method: str, path: str, body=None, headers=None):
        """Returns (status, parsed JSON or None). Network errors give status -1."""
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method)
        request.add_header("Content-Type", "application/json")
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        for name, value in (headers or {}).items():
            request.add_header(name, value)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                status, raw = response.status, response.read()
        except urllib.error.HTTPError as err:
            status, raw = err.code, err.read()
        except OSError:
            return -1, None
        try:
            return status, json.loads(raw) if raw else None
        except ValueError:
            return status, None

    def must(self, method: str, path: str, body=None, ok=(200, 201)):
        status, payload = self.call(method, path, body)
        if status not in ok:
            detail = (
                (payload or {}).get("detail", payload) if status > 0 else "no answer"
            )
            sys.exit(f"{method} {path} failed: HTTP {status}: {detail}")
        return payload

    def login(self, user: str, pin: str) -> None:
        self.token = self.must("POST", "/auth/login", {"username": user, "pin": pin})[
            "session_id"
        ]


# ---------------------------------------------------------------------------
# Roster commands
# ---------------------------------------------------------------------------


def student_ids(api: Api) -> dict[str, int]:
    users = api.must("GET", "/staff/users")["users"]
    return {u["username"]: u["id"] for u in users if u.get("role") == "student"}


def cmd_list(api: Api, _args) -> None:
    devices = api.must("GET", "/staff/devices")["devices"]
    if not devices:
        print("No clickers yet. Power one on near the TutorBox: it enrolls by itself.")
        return
    print(
        f"{'CLICKER':<14} {'STUDENT':<16} {'STATE':<9} {'SIGNAL':>7} "
        f"{'BATTERY':>8}  FIRMWARE  LAST SEEN (UTC)"
    )
    for d in devices:
        state = "online" if d.get("online") else "offline"
        if not d.get("enrolled"):
            state = "new"
        signal = f"{d['rssi']} dBm" if d.get("rssi") is not None else "-"
        battery = f"{d['battery_mv'] / 1000:.2f} V" if d.get("battery_mv") else "-"
        print(
            f"{d['device_id']:<14} {d.get('assigned_username') or '(none)':<16} "
            f"{state:<9} {signal:>7} {battery:>8}  {d.get('firmware') or '-':<9} "
            f"{d.get('last_seen_at') or '-'}"
        )
    online = sum(1 for d in devices if d.get("online"))
    print(f"\n{len(devices)} clickers, {online} online.")


def assign_one(api: Api, device: str, username: str, ids: dict[str, int]) -> None:
    if username not in ids:
        sys.exit(f"No student called '{username}'. Create the account first.")
    api.must("POST", f"/staff/devices/{device}/assign", {"user_id": ids[username]})
    print(f"{device} -> {username}")


def cmd_assign(api: Api, args) -> None:
    assign_one(api, args.device, args.username, student_ids(api))


def cmd_assign_csv(api: Api, args) -> None:
    ids = student_ids(api)
    with open(args.file, newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if len(row) >= 2 and not row[0].startswith("#") and row[0].strip():
                assign_one(api, row[0].strip(), row[1].strip(), ids)


def cmd_unassign(api: Api, args) -> None:
    api.must("POST", f"/staff/devices/{args.device}/unassign")
    print(f"{args.device} unassigned")


def cmd_forget(api: Api, args) -> None:
    api.must("DELETE", f"/staff/devices/{args.device}")
    print(f"{args.device} removed: it enrolls again (unassigned) on its next check-in")


# ---------------------------------------------------------------------------
# Fleet simulator: N fake clickers speaking the firmware's protocol
# ---------------------------------------------------------------------------


class FakeClicker(threading.Thread):
    def __init__(self, api: Api, device: str, stop: threading.Event, stats: dict):
        super().__init__(daemon=True)
        self.api, self.device, self.stop, self.stats = api, device, stop, stats
        self.headers = {
            "X-Clicker-Id": device,
            "X-Clicker-Secret": secrets.token_hex(16),
        }
        self.answered: set[str] = set()

    def timed(self, kind: str, path: str, body: dict):
        start = time.perf_counter()
        status, payload = self.api.call("POST", path, body, self.headers)
        with self.stats["lock"]:
            self.stats[kind].append((time.perf_counter() - start) * 1000)
            self.stats["codes"][f"{kind} {status}"] = (
                self.stats["codes"].get(f"{kind} {status}", 0) + 1
            )
        return status, payload

    def run(self) -> None:
        while not self.stop.is_set():
            status, view = self.timed(
                "checkin", "/clicker/checkin", {"firmware": "sim"}
            )
            round_id = (view or {}).get("round_id")
            if (
                status == 200
                and view.get("round_open")
                and not view.get("voted")
                and round_id not in self.answered
            ):
                self.stop.wait(random.uniform(0.3, 2.5))  # a student thinking
                self.answered.add(round_id)
                self.timed(
                    "vote",
                    "/clicker/vote",
                    {"round_id": round_id, "selected_option": random.choice("ABCD")},
                )
            self.stop.wait(1.0)


def percentile(values: list[float], share: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(share * len(ordered)))] if ordered else 0.0


def cmd_simulate(api: Api, args) -> None:
    stop = threading.Event()
    stats = {"lock": threading.Lock(), "checkin": [], "vote": [], "codes": {}}
    fleet = [
        FakeClicker(api, f"SIM-{index:04d}", stop, stats)
        for index in range(1, args.count + 1)
    ]
    for clicker in fleet:  # enroll them all first
        clicker.timed("checkin", "/clicker/checkin", {"firmware": "sim"})
    if args.auto_assign:
        ids = student_ids(api)
        for clicker in fleet:
            name = f"sim_{clicker.device[-4:]}"
            if name not in ids:
                api.must("POST", "/staff/users", {"username": name, "pin": "4321"})
                ids = student_ids(api)
            api.must(
                "POST",
                f"/staff/devices/{clicker.device}/assign",
                {"user_id": ids[name]},
            )
    print(
        f"{args.count} simulated clickers polling for {args.seconds} s. "
        "Start a match on /maestro/ to see them vote."
    )
    for clicker in fleet:
        clicker.start()
    try:
        stop.wait(args.seconds)
    except KeyboardInterrupt:
        pass
    stop.set()
    for clicker in fleet:
        clicker.join(timeout=6)
    for kind in ("checkin", "vote"):
        times = stats[kind]
        if times:
            print(
                f"{kind:<8} n={len(times):<5} p50={statistics.median(times):6.1f} ms  "
                f"p95={percentile(times, 0.95):6.1f} ms  max={max(times):6.1f} ms"
            )
    print("HTTP status counts:", dict(sorted(stats["codes"].items())))


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Manage TutorBox hardware clickers.")
    parser.add_argument(
        "--server", default=os.environ.get("TUTORBOX_URL", "http://192.168.8.2")
    )
    parser.add_argument("--user", default="teacher1", help="teacher or admin username")
    parser.add_argument("--pin", default=os.environ.get("TUTORBOX_PIN"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="clickers, students, online state, battery")
    p = sub.add_parser("assign", help="give a clicker to a student")
    p.add_argument("device")
    p.add_argument("username")
    p = sub.add_parser("assign-csv", help="assign from a CSV file: device,username")
    p.add_argument("file")
    p = sub.add_parser("unassign", help="take a clicker away from its student")
    p.add_argument("device")
    p = sub.add_parser("forget", help="remove a clicker so it re-enrolls")
    p.add_argument("device")
    p = sub.add_parser("simulate", help="N fake clickers, for load tests")
    p.add_argument("count", type=int)
    p.add_argument("--seconds", type=int, default=60)
    p.add_argument(
        "--auto-assign",
        action="store_true",
        help="create students sim_0001... and assign one per clicker",
    )
    args = parser.parse_args(argv)

    api = Api(args.server)
    api.login(args.user, args.pin or getpass.getpass(f"PIN for {args.user}: "))
    commands = {
        "list": cmd_list,
        "assign": cmd_assign,
        "assign-csv": cmd_assign_csv,
        "unassign": cmd_unassign,
        "forget": cmd_forget,
        "simulate": cmd_simulate,
    }
    commands[args.command](api, args)


if __name__ == "__main__":
    main()
