"""Subprocess lifecycle and stdio pipe manager for Qwen3-TTS daemon."""

from __future__ import annotations

import logging
import queue
import subprocess
import threading
from pathlib import Path

from core.tts.exceptions import TTSSynthesisError, TTSUnavailableError

__all__ = ["QwenDaemonClient"]

logger = logging.getLogger(__name__)


class QwenDaemonClient:
    """Manages a persistent llama-tts-daemon subprocess via stdin/stdout."""

    def __init__(self, cmd: list[str], startup_timeout: float = 30.0) -> None:
        self._cmd = cmd
        self._startup_timeout = startup_timeout
        self._process: subprocess.Popen[str] | None = None
        self._stdout_queue: queue.Queue[str] = queue.Queue()
        self._reader_thread: threading.Thread | None = None
        self._start()

    def _start(self) -> None:
        try:
            self._process = subprocess.Popen(
                self._cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as err:
            raise TTSUnavailableError(f"Failed to spawn Qwen daemon: {err}") from err

        self._reader_thread = threading.Thread(
            target=self._read_stdout,
            daemon=True,
        )
        self._reader_thread.start()
        self._wait_for_ready()

    def _read_stdout(self) -> None:
        if self._process and self._process.stdout:
            for line in iter(self._process.stdout.readline, ""):
                self._stdout_queue.put(line.strip())
        self._stdout_queue.put("")

    def _wait_for_ready(self) -> None:
        try:
            line = self._stdout_queue.get(timeout=self._startup_timeout)
            if line != "READY":
                err = self._read_stderr()
                self.close()
                msg = f"Qwen daemon startup failed: {line}. {err}".strip()
                raise TTSUnavailableError(msg)
        except queue.Empty as err:
            self.close()
            msg = f"Qwen daemon timed out after {self._startup_timeout}s waiting for READY."
            raise TTSUnavailableError(msg) from err

    def _read_stderr(self) -> str:
        return (
            self._process.stderr.read()
            if self._process and self._process.stderr
            else ""
        )

    def is_alive(self) -> bool:
        """Returns True if the daemon subprocess is actively running."""
        return self._process is not None and self._process.poll() is None

    def synthesize(
        self,
        lang: str,
        out_wav_path: Path,
        text: str,
        timeout_seconds: float = 10.0,
    ) -> str:
        """Dispatches a SYNTH command to daemon and awaits completion response."""
        if not self.is_alive() or not self._process or not self._process.stdin:
            raise TTSSynthesisError("Qwen daemon process is not running.")

        clean_text = text.replace("\t", " ").replace("\n", " ").strip()
        command = f"SYNTH\t{lang}\t{out_wav_path}\t{clean_text}\n"

        try:
            self._process.stdin.write(command)
            self._process.stdin.flush()
            response = self._stdout_queue.get(timeout=timeout_seconds)
        except queue.Empty as err:
            self.close()
            msg = f"Qwen daemon synthesis timed out after {timeout_seconds}s."
            raise TTSSynthesisError(msg) from err
        except OSError as err:
            self.close()
            msg = f"Failed to communicate with Qwen daemon: {err}"
            raise TTSSynthesisError(msg) from err

        if not response:
            err = self._read_stderr()
            self.close()
            msg = f"Qwen daemon terminated unexpectedly. {err}".strip()
            raise TTSSynthesisError(msg)

        if not response.startswith("DONE"):
            raise TTSSynthesisError(f"Qwen daemon synthesis failed: {response}")

        return response

    def close(self) -> None:
        """Terminates the daemon subprocess and reclaims OS resources."""
        if self._process:
            proc = self._process
            self._process = None
            try:
                if proc.poll() is None and proc.stdin:
                    proc.stdin.write("QUIT\n")
                    proc.stdin.flush()
                proc.wait(timeout=2.0)
            except (OSError, subprocess.SubprocessError):
                proc.kill()
