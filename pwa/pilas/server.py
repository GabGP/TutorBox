"""Local classroom quiz server. Stdlib only.

One port (TUTORBOX_PORT, default 190), routed by URL prefix:
  /maestro/   host / teacher  -> host.html + control API
  /alumno/    student players -> student.html + join/vote API
  /mando/     ESP32 clickers  -> POST /mando/vote {device_id, choice}   (reserved, same vote path)
  /pantalla/  HDMI class screen -> screen.html (question + timer only, never per-student votes)
  /           -> /alumno/

Questions come from the backend's local LLM (POST /api/v1/quiz/generate) as a teacher;
the seed bank only fills in when the backend or model is unreachable.
  TUTORBOX_API   default http://127.0.0.1:8000/api/v1
  TUTORBOX_USER / TUTORBOX_PIN   teacher credentials, default teacher1 / 1234

Run from this folder with the backend's Python (seed bank needs pydantic):
  python server.py            # serves on 0.0.0.0
  python server.py --selftest # runs the session logic check
On Linux ports < 1024 need root or `setcap cap_net_bind_service=+ep`.
"""

import json
import os
import random
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
from urllib.request import Request, urlopen

HERE = Path(__file__).parent
PORT = int(os.environ.get("TUTORBOX_PORT", 190))
CHOICES = ("A", "B", "C", "D")
QUESTION_SECONDS = 20
STATIC = {"/tb.css": "text/css"}
API = os.environ.get("TUTORBOX_API", "http://127.0.0.1:8000/api/v1")
TEACHER = (os.environ.get("TUTORBOX_USER", "teacher1"), os.environ.get("TUTORBOX_PIN", "1234"))


def load_bank() -> list[dict]:
    sys.path.insert(0, str(HERE.parents[1] / "backend" / "src"))
    from modes.quiz.seed_data import SEED_QUESTIONS

    return [q.model_dump() for q in SEED_QUESTIONS]


def api(path: str, body: dict | None = None, token: str | None = None) -> dict:
    """One call to the TutorBox backend. Raises on network/HTTP errors."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(API + path, data=json.dumps(body).encode() if body is not None else None, headers=headers)
    with urlopen(req, timeout=180) as r:
        return json.load(r)


def fetch_topics(bank: list[dict]) -> list[str]:
    try:
        return [t["name"] for t in api("/quiz/topics")]
    except OSError:
        return sorted({q["topic"] for q in bank})


def generate_question(topic: str, token: str) -> dict:
    return api("/quiz/generate", {"topic": topic}, token)["question"]


class Session:
    """Question lifecycle: lobby -> question (open) -> revealed -> ... -> finished."""

    def __init__(self, bank: list[dict], topic_ids: list[str] | None = None, generate=generate_question):
        self.bank = bank
        self.topic_ids = topic_ids or sorted({q["topic"] for q in bank})
        self.generate = generate
        self.lock = threading.Lock()
        self.gen = 0  # bumped on reset so a stale generator thread drops its results
        self.reset()

    def reset(self):
        self.phase = "lobby"
        self.questions: list[dict] = []
        self.total = 0
        self.fallback = 0  # questions served from the seed bank because the model failed
        self.generating = False
        self.gen += 1
        self.index = -1
        self.players: dict[str, int] = {}  # name -> score
        self.votes: dict[str, str] = {}  # name -> choice (current question)
        self.voted_ever: set[str] = set()
        self.history: list[dict] = []  # one entry per revealed question (stats)
        self.started_at = 0.0

    def start(self, count: int = 5, topic: str | None = None):
        """Enter 'generating'; a thread asks the model one question at a time and the game
        advances as soon as the first one lands (teacher waits again only if it runs ahead)."""
        self.questions, self.index, self.history, self.voted_ever = [], -1, [], set()
        self.total, self.fallback, self.generating, self.phase = count, 0, True, "generating"
        for n in self.players:
            self.players[n] = 0
        threading.Thread(target=self._produce, args=(count, topic, self.gen), daemon=True).start()

    def _produce(self, count: int, topic: str | None, gen: int):
        try:
            token = api("/auth/login", {"username": TEACHER[0], "pin": TEACHER[1]})["session_id"]
        except (OSError, KeyError):
            token = None
        for _ in range(count):
            t = topic or random.choice(self.topic_ids)
            q, fell = None, False
            if token:
                try:
                    q = self.generate(t, token)
                except (OSError, KeyError, ValueError):
                    pass
            with self.lock:
                if gen != self.gen:
                    return  # reset happened while we were generating
                if q is None:  # model unreachable/invalid -> seed bank, never a blank slot
                    used = {x["question_text"] for x in self.questions}
                    pool = [x for x in self.bank if x["topic"] == t and x["question_text"] not in used]
                    q, fell = (random.choice(pool) if pool else None), True
                if q:
                    self.questions.append(q)
                    self.fallback += fell
                    if self.phase == "generating":
                        self.next()
        with self.lock:
            if gen == self.gen:
                self.generating = False
                self.total = len(self.questions)
                if self.phase == "generating":
                    self.next()

    def next(self):
        if self.index + 1 >= len(self.questions):
            self.phase = "generating" if self.generating else "finished"
            return
        self.index += 1
        self.votes = {}
        self.phase = "question"
        self.started_at = time.monotonic()

    def remaining(self) -> int:
        return max(0, round(QUESTION_SECONDS - (time.monotonic() - self.started_at)))

    def tick(self):
        """Lazy timer: the first state read after the window closes reveals the answer."""
        if self.phase == "question" and self.remaining() == 0:
            self.reveal()

    def reveal(self):
        if self.phase != "question":
            return
        self.phase = "revealed"
        q = self.question
        correct = q["correct_option"]
        for name, choice in self.votes.items():
            if choice == correct and name in self.players:
                self.players[name] += 1
        self.history.append({
            "text": q["question_text"],
            "correct": correct,
            "correct_text": q["options"][correct],
            "tally": self.tally(),
            "voters": len(self.votes),
            "top_distractor": self.top_distractor(),
        })

    def join(self, name: str):
        self.players.setdefault(name, 0)

    def vote(self, name: str, choice: str) -> bool:
        if self.phase != "question" or choice not in CHOICES or not name or name in self.votes:
            return False  # first press locks (design: "Respuesta enviada")
        self.players.setdefault(name, 0)
        self.votes[name] = choice
        self.voted_ever.add(name)
        return True

    @property
    def question(self) -> dict | None:
        return self.questions[self.index] if 0 <= self.index < len(self.questions) else None

    def tally(self) -> dict[str, int]:
        t = dict.fromkeys(CHOICES, 0)
        for c in self.votes.values():
            t[c] += 1
        return t

    def top_distractor(self) -> dict | None:
        """Most-chosen wrong option, with its count and misconception."""
        q = self.question
        if not q or not self.votes:
            return None
        choice, count = max(
            ((c, n) for c, n in self.tally().items() if c != q["correct_option"]), key=lambda cn: cn[1]
        )
        if not count:
            return None
        return {"choice": choice, "count": count, "text": q["options"][choice], **q["distractors"][choice]}

    def majority_distractor(self) -> dict | None:
        """The >51% rule: a single distractor chosen by more than half of voters."""
        d = self.top_distractor()
        return d if d and d["count"] * 100 > 51 * len(self.votes) else None

    def report(self) -> dict:
        """Group summary for the stats step and the CSV export."""
        h = self.history
        answered = sum(x["voters"] for x in h)
        correct = sum(x["tally"][x["correct"]] for x in h)
        hard = sorted(
            ({"text": x["text"], "pct": round(100 * x["tally"][x["correct"]] / x["voters"]) if x["voters"] else 0} for x in h),
            key=lambda x: x["pct"],
        )
        errors = [
            {"question": x["text"], **x["top_distractor"]}  # text = the chosen wrong option
            for x in h
            if x["top_distractor"] and x["top_distractor"]["count"] >= 2
        ]
        return {
            "average": round(100 * correct / answered) if answered else 0,
            "participation": [len(self.voted_ever), len(self.players)],
            "ranking": sorted(self.players.items(), key=lambda kv: (-kv[1], kv[0])),
            "hardest": hard[:3],
            "errors": sorted(errors, key=lambda e: -e["count"])[:3],
        }

    def report_csv(self) -> str:
        r = self.report()
        lines = ["alumno,aciertos,total"] + [f"{n},{p},{len(self.questions)}" for n, p in r["ranking"]]
        lines += ["", "pregunta,correcta,respondieron,aciertos"]
        lines += [
            f'"{x["text"]}",{x["correct"]} {x["correct_text"]},{x["voters"]},{x["tally"][x["correct"]]}'
            for x in self.history
        ]
        return "\n".join(lines) + "\n"

    def public_state(self, name: str | None = None) -> dict:
        self.tick()
        q = self.question
        state = {
            "phase": self.phase,
            "index": self.index,
            "total": self.total,
            "players": len(self.players),
            "voted": len(self.votes),
            "my_choice": self.votes.get(name) if name else None,
            "score": self.players.get(name) if name else None,
        }
        if q and self.phase in ("question", "revealed"):
            state["question"] = {"text": q["question_text"], "options": q["options"]}
        if self.phase == "question":
            state["remaining"] = self.remaining()
        if q and self.phase == "revealed":
            state["correct"] = q["correct_option"]
            mine = self.votes.get(name or "", "")
            state["explanation"] = q["distractors"].get(mine, {}).get("explanation")
        return state

    def host_state(self) -> dict:
        state = self.public_state()
        state.update(
            topics=self.topic_ids,
            ready=len(self.questions),
            fallback=self.fallback,
            tally=self.tally(),
            scores=sorted(self.players.items(), key=lambda kv: -kv[1]),
            votes=self.votes,
        )
        if self.question:
            state["correct"] = self.question["correct_option"]
            state["majority_distractor"] = self.majority_distractor()
        if self.phase == "finished":
            state["report"] = self.report()
        return state

    def screen_state(self) -> dict:
        """HDMI display: question + timer only; never per-student votes."""
        state = self.public_state()
        if self.phase == "finished":
            state["podium"] = self.report()["ranking"][:3]
        return state


SESSION: Session


class Student:
    """One role = one URL prefix. Subclasses override `page`, `state`, `action`."""

    page = "student.html"

    def state(self, name):
        return SESSION.public_state(name)

    def action(self, path, data, name) -> bool:
        if path == "join" and name:
            SESSION.join(name)
            return True
        if path == "vote":
            return SESSION.vote(name, data.get("choice"))
        return False


class Host(Student):
    page = "host.html"

    def state(self, name):
        return SESSION.host_state()

    def action(self, path, data, name) -> bool:
        if path == "start" and SESSION.phase in ("lobby", "finished"):
            SESSION.start(int(data.get("count", 5)), data.get("topic") or None)
        elif path == "next":
            SESSION.next()
        elif path == "reveal":
            SESSION.reveal()
        elif path == "reset":
            SESSION.reset()
        elif path == "speak":
            pass  # ponytail: TTS seam — body {lang: "es"|"quc", text}; wire to the backend voice service later
        else:
            return False
        return True


class Screen(Student):
    page = "screen.html"

    def state(self, name):
        return SESSION.screen_state()

    def action(self, path, data, name) -> bool:
        return False


class Clicker(Student):
    """ESP32 transport: POST /mando/vote {"device_id": "7", "choice": "B"}. Player = "Clicker #7"."""

    def action(self, path, data, name) -> bool:
        if path == "vote" and data.get("device_id"):
            return SESSION.vote(f"Clicker #{data['device_id']}", data.get("choice"))
        return False


ROLES = {"maestro": Host(), "alumno": Student(), "mando": Clicker(), "pantalla": Screen()}


class Handler(BaseHTTPRequestHandler):
    """Single port. /<role>/ serves the page, /<role>/state polls, /<role>/<action> posts."""

    def log_message(self, *_):
        pass

    def send_json(self, data, code=200):
        self.send_bytes(json.dumps(data).encode(), "application/json", code)

    def send_bytes(self, body: bytes, ctype: str, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
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

    def route(self, path: str):
        """'/maestro/state' -> (Host(), 'state'); unknown role -> (None, ...)."""
        role, _, sub = path.strip("/").partition("/")
        return ROLES.get(role), sub

    def do_GET(self):
        path, _, query = self.path.partition("?")
        role, sub = self.route(path)
        if path in STATIC:
            self.send_bytes((HERE / path[1:]).read_bytes(), STATIC[path])
        elif path == "/" or (role and not sub and not path.endswith("/")):
            self.send_response(302)  # trailing slash so the pages' relative fetch('state') resolves
            self.send_header("Location", "/alumno/" if path == "/" else path + "/")
            self.end_headers()
        elif role and not sub:
            self.send_bytes((HERE / role.page).read_bytes(), "text/html; charset=utf-8")
        elif role and sub == "state":
            name = (parse_qs(query).get("name") or [None])[0]
            with SESSION.lock:
                self.send_json(role.state(name))
        elif sub == "report.csv" and isinstance(role, Host):
            with SESSION.lock:
                self.send_bytes(SESSION.report_csv().encode(), "text/csv; charset=utf-8")
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        role, sub = self.route(self.path)
        if not role:
            return self.send_json({"error": "not found"}, 404)
        data = self.read_json()
        name = str(data.get("name", "")).strip()[:24]
        with SESSION.lock:
            ok = role.action(sub, data, name)
            self.send_json({"ok": ok, **role.state(name or None)}, 200 if ok else 409)


def serve():
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    for role in ROLES:
        print(f"http://0.0.0.0:{PORT}/{role}/", flush=True)
    srv.serve_forever()


def selftest():
    q = {
        "question_text": "2+2?",
        "topic": "t",
        "options": {"A": "3", "B": "4", "C": "5", "D": "22"},
        "correct_option": "B",
        "distractors": {k: {"misconception": "m", "explanation": f"why not {k}"} for k in "ACD"},
    }
    s = Session([q], generate=lambda t, tok: dict(q, question_text="from the model"))
    assert not s.vote("ana", "B"), "no voting in lobby"
    s.join("ana"), s.join("beto"), s.join("cai")
    s.start(1)
    assert s.phase == "generating" and s.public_state("ana")["total"] == 1
    s._produce(1, None, s.gen)  # the thread's job; backend login fails offline -> seed bank fills in
    assert s.phase == "question" and s.fallback == 1 and s.host_state()["ready"] == 1
    assert s.public_state("ana")["question"]["options"]["B"] == "4"
    assert "correct" not in s.public_state("ana"), "correct answer hidden while open"
    assert s.public_state("ana")["remaining"] == QUESTION_SECONDS
    assert s.vote("ana", "B") and s.vote("beto", "D") and s.vote("cai", "D")
    assert s.vote("ana", "A") is False, "first press locks"
    assert s.vote("cai", "Z") is False and s.vote("", "A") is False
    assert s.majority_distractor()["choice"] == "D", ">51% rule"
    s.started_at -= QUESTION_SECONDS  # fast-forward the clock
    st = s.public_state("cai")
    assert s.phase == "revealed", "timer auto-reveals"
    assert st["correct"] == "B" and st["explanation"] == "why not D" and st["score"] == 0
    assert s.public_state("ana")["score"] == 1
    s.next()
    assert s.phase == "finished"
    r = s.report()
    assert r["average"] == 33 and r["participation"] == [3, 3] and r["ranking"][0] == ("ana", 1)
    assert r["hardest"][0]["pct"] == 33 and r["errors"][0]["choice"] == "D" and r["errors"][0]["count"] == 2
    assert s.screen_state()["podium"][0][0] == "ana" and "votes" not in s.screen_state()
    assert "ana,1,1" in s.report_csv()
    s.generating, s.phase, s.index = True, "revealed", 0  # teacher outruns the model
    s.next()
    assert s.phase == "generating"
    s.questions.append(q), s.next()
    assert s.phase == "question" and s.index == 1
    s.reset()
    assert s.phase == "lobby" and s.total == 0
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        bank = load_bank()
        SESSION = Session(bank, fetch_topics(bank))
        print(f"backend {API} · topics {SESSION.topic_ids} · {len(bank)} fallback questions", flush=True)
        serve()
