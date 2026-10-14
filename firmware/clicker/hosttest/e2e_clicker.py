"""The clicker side of the end-to-end test: the simulated clicker process (sim/), what
it prints, and the secret it keeps in its simulated flash."""

import os
import queue
import re
import subprocess
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIM = HERE / "build" / "clicker_sim"


class Clicker:
    """The simulated clicker process, with a reader thread and expect()."""

    def __init__(self, port: int, nvs: str, held: str = ""):
        env = dict(
            os.environ, CLICKER_SIM_SERVER=f"127.0.0.1:{port}", CLICKER_SIM_NVS=nvs
        )
        if held:
            env["CLICKER_SIM_HELD"] = held  # buttons down from power-on
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
        self.printed: list[str] = []  # every line, read by expect() or not
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        for line in self.proc.stdout:
            self.printed.append(line.rstrip("\n"))
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


def stored_secret(nvs: str) -> str | None:
    """The secret in the simulated flash, as the clicker stored it."""
    try:
        with open(nvs, encoding="utf-8") as file:
            for line in file:
                if line.startswith("secret="):
                    return line.strip().split("=", 1)[1]
    except FileNotFoundError:
        pass
    return None
