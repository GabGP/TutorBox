"""Local classroom quiz server. Stdlib only.

Ports (fixed by classroom convention):
  190  host / teacher  -> host.html + control API
  195  student players -> student.html + join/vote API
  196  ESP32 clickers  -> POST /vote {device_id, choice}   (reserved, same vote path)

Run from this folder with the backend's Python (seed bank needs pydantic):
  python server.py            # serves on 0.0.0.0
  python server.py --selftest # runs the session logic check
On Linux ports < 1024 need root or `setcap cap_net_bind_service=+ep`.
"""

import json
import random
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

HERE = Path(__file__).parent
PORT_HOST, PORT_STUDENT, PORT_CLICKER = 190, 195, 196
CHOICES = ("A", "B", "C", "D")


def load_bank() -> list[dict]:
    sys.path.insert(0, str(HERE.parents[1] / "backend" / "src"))
    from quiz.seed_data import SEED_QUESTIONS

    return [q.model_dump() for q in SEED_QUESTIONS]


class Session:
    """Question lifecycle: lobby -> question (open) -> revealed -> ... -> finished."""

    def __init__(self, bank: list[dict]):
        self.bank = bank
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.phase = "lobby"
        self.questions: list[dict] = []
        self.index = -1
        self.players: dict[str, int] = {}  # name -> score
        self.votes: dict[str, str] = {}  # name -> choice (current question)

    def topics(self) -> list[str]:
        return sorted({q["topic"] for q in self.bank})

    def start(self, count: int = 5, topic: str | None = None):
        pool = [q for q in self.bank if not topic or q["topic"] == topic]
        self.questions = random.sample(pool, min(count, len(pool)))
        self.index = -1
        for n in self.players:
            self.players[n] = 0
        self.next()

    def next(self):
        if self.index + 1 >= len(self.questions):
            self.phase = "finished"
            return
        self.index += 1
        self.votes = {}
        self.phase = "question"

    def reveal(self):
        if self.phase != "question":
            return
        self.phase = "revealed"
        correct = self.question["correct_option"]
        for name, choice in self.votes.items():
            if choice == correct and name in self.players:
                self.players[name] += 1

    def join(self, name: str):
        self.players.setdefault(name, 0)

    def vote(self, name: str, choice: str) -> bool:
        if self.phase != "question" or choice not in CHOICES or not name:
            return False
        self.players.setdefault(name, 0)
        self.votes[name] = choice  # ponytail: last press wins inside the window
        return True

    @property
    def question(self) -> dict | None:
        return self.questions[self.index] if 0 <= self.index < len(self.questions) else None

    def tally(self) -> dict[str, int]:
        t = dict.fromkeys(CHOICES, 0)
        for c in self.votes.values():
            t[c] += 1
        return t

    def majority_distractor(self) -> dict | None:
        """The >51% rule: a single distractor chosen by more than half of voters."""
        q, n = self.question, len(self.votes)
        if not q or not n:
            return None
        for choice, count in self.tally().items():
            if choice != q["correct_option"] and count * 100 > 51 * n:
                return {"choice": choice, **q["distractors"][choice]}
        return None

    def public_state(self, name: str | None = None) -> dict:
        q = self.question
        state = {
            "phase": self.phase,
            "index": self.index,
            "total": len(self.questions),
            "players": len(self.players),
            "voted": len(self.votes),
            "my_choice": self.votes.get(name) if name else None,
            "score": self.players.get(name) if name else None,
        }
        if q and self.phase in ("question", "revealed"):
            state["question"] = {"text": q["question_text"], "options": q["options"]}
        if q and self.phase == "revealed":
            state["correct"] = q["correct_option"]
            mine = self.votes.get(name or "", "")
            state["explanation"] = q["distractors"].get(mine, {}).get("explanation")
        return state

    def host_state(self) -> dict:
        state = self.public_state()
        state.update(
            topics=self.topics(),
            tally=self.tally(),
            scores=sorted(self.players.items(), key=lambda kv: -kv[1]),
            votes=self.votes,
        )
        if self.question:
            state["correct"] = self.question["correct_option"]
            state["distractors"] = self.question["distractors"]
            state["majority_distractor"] = self.majority_distractor()
        return state


SESSION: Session


class Handler(BaseHTTPRequestHandler):
    """Student port. Subclasses override `page`, `state`, `action`."""

    page = "student.html"

    def log_message(self, *_):
        pass

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return {}

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/":
            body = (HERE / self.page).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/state":
            name = (parse_qs(query).get("name") or [None])[0]
            with SESSION.lock:
                self.send_json(self.state(name))
        else:
            self.send_json({"error": "not found"}, 404)

    def state(self, name):
        return SESSION.public_state(name)

    def do_POST(self):
        data = self.read_json()
        name = str(data.get("name", "")).strip()[:24]
        with SESSION.lock:
            ok = self.action(self.path, data, name)
            self.send_json({"ok": ok, **self.state(name or None)}, 200 if ok else 409)

    def action(self, path, data, name) -> bool:
        if path == "/join" and name:
            SESSION.join(name)
            return True
        if path == "/vote":
            return SESSION.vote(name, data.get("choice"))
        return False


class HostHandler(Handler):
    page = "host.html"

    def state(self, name):
        return SESSION.host_state()

    def action(self, path, data, name) -> bool:
        if path == "/start":
            SESSION.start(int(data.get("count", 5)), data.get("topic") or None)
        elif path == "/next":
            SESSION.next()
        elif path == "/reveal":
            SESSION.reveal()
        elif path == "/reset":
            SESSION.reset()
        else:
            return False
        return True


class ClickerHandler(Handler):
    """ESP32 transport: POST /vote {"device_id": "7", "choice": "B"}. Player = "Clicker #7"."""

    def action(self, path, data, name) -> bool:
        if path == "/vote" and data.get("device_id"):
            return SESSION.vote(f"Clicker #{data['device_id']}", data.get("choice"))
        return False


def serve():
    for port, handler in ((PORT_HOST, HostHandler), (PORT_STUDENT, Handler), (PORT_CLICKER, ClickerHandler)):
        srv = ThreadingHTTPServer(("0.0.0.0", port), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        print(f"{handler.__name__:15s} http://0.0.0.0:{port}/", flush=True)
    threading.Event().wait()


def selftest():
    q = {
        "question_text": "2+2?",
        "topic": "t",
        "options": {"A": "3", "B": "4", "C": "5", "D": "22"},
        "correct_option": "B",
        "distractors": {k: {"misconception": "m", "explanation": f"why not {k}"} for k in "ACD"},
    }
    s = Session([q])
    assert not s.vote("ana", "B"), "no voting in lobby"
    s.join("ana"), s.join("beto"), s.join("cai")
    s.start(1)
    assert s.phase == "question" and s.public_state("ana")["question"]["options"]["B"] == "4"
    assert "correct" not in s.public_state("ana"), "correct answer hidden while open"
    assert s.vote("ana", "B") and s.vote("beto", "D") and s.vote("cai", "D")
    assert s.vote("cai", "Z") is False and s.vote("", "A") is False
    assert s.majority_distractor()["choice"] == "D", ">51% rule"
    s.reveal()
    st = s.public_state("cai")
    assert st["correct"] == "B" and st["explanation"] == "why not D" and st["score"] == 0
    assert s.public_state("ana")["score"] == 1
    s.next()
    assert s.phase == "finished"
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        SESSION = Session(load_bank())
        print(f"loaded {len(SESSION.bank)} questions", flush=True)
        serve()
