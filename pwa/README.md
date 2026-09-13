# TutorBox Frontend (PWA)

Classroom web client hosted directly on the NVIDIA Jetson Orin Nano appliance (vanilla HTML/JS today; a React/Vite PWA is a later milestone).

<div align="center">

| 🏠 [TutorBox](../README.md) | 📚 [Docs](../docs/README.md) | ⚙️ [Backend](../backend/README.md) | 📱 **PWA** | 🔌 [Infra](../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Frontend (PWA) Hub** • **Related:** [Docs Hub](../docs/README.md) • [REST API Hub](../docs/api/README.md) • [Three Modes](../docs/architecture/three-modes.md)

</div>

---

## 1. Pilas — the classroom quiz client (`pilas/`)

Pilas is the shipped Classroom Quiz client: three vanilla HTML pages plus a shared `static/tb.js`,
served by the FastAPI backend itself (`backend/src/main.py` mounts `pwa/pilas` per folder), so every
page talks to `/api/v1` on the same origin. There is no build step and no state of its own: the
backend session engine is the only source of truth and the pages poll it once per second.

| URL | Who | What it does |
| :--- | :--- | :--- |
| `/maestro/` | Teacher (role `teacher`/`admin`) | Login → pick a topic → number of questions → the local model writes every question (`POST /quiz/generate`, no seed bank) → student roster → start the match → live count, close/reveal/next → group summary + CSV. When one wrong answer takes >51% of the class, the device reads the misconception explanation out loud (offline espeak-ng, Latin American Spanish). |
| `/alumno/` | Students | **Opens by itself when a phone joins the `TutorBox` Wi-Fi** ([captive portal](../infra/captive-portal.md)). Login or self-signup (forced PIN change when the teacher reset it) → auto-join the current match → A–D vote (first press locks) → result with the explanation for the chosen distractor → final score. |
| `/pantalla/` | HDMI classroom screen | Question + countdown + vote count, then the correct answer with the aggregate bars. Never per-student votes. |
| `/` | — | Redirects to `/alumno/` (to `http://tutorbox/alumno/` when reached through any other name). |

### Run it

```bash
sudo apt install espeak-ng                           # offline voice for the >51% intervention
cd backend
python -m uvicorn src.main:app --host 0.0.0.0        # teacher: http://<appliance-ip>:8000/maestro/
# classroom: nginx publishes the same process on :80 → http://tutorbox/maestro/ (infra/nginx/tutorbox.conf)
```

Bootstrap teacher: `teacher1` / `1234` (`SEED_TEACHER_*` in `.env`). The model must be reachable at
`SLM_BASE_URL`; when a generation fails the slot is skipped and the teacher is told — nothing is
served from the question bank.

### Endpoints used

| Endpoint | Page |
| :--- | :--- |
| `GET /health` | teacher login indicator |
| `POST /auth/login`, `POST /auth/logout`, `GET /users/me`, `PATCH /users/me/pin` | all logins, session restore, forced PIN rotation |
| `POST /users/signup` | student "Crear cuenta" |
| `GET /staff/users`, `POST /staff/users`, `POST /staff/users/{id}/reset-pin` | teacher roster |
| `GET /quiz/topics`, `POST /quiz/generate` (`save_to_bank: true`), `GET /quiz/generation-metrics` | topic cards, question generation, ETA |
| `POST /session`, `/start`, `/close`, `/reveal`, `/next`, `GET /session/{id}/report` | teacher match control |
| `GET /session/{id}/speech?lang=es` | teacher device: espeak-ng (es-419) WAV read out loud when the >51% rule fires |
| `GET /session/current`, `GET /session/{id}` | students and screen (polling), teacher (own match) |
| `POST /session/{id}/vote` | student vote |

Client-side only (per browser `localStorage`): the bearer token, the teacher's current session id and
per-round reveal history (for the summary page), and each student's own votes/score. The ESP32
clicker transport (Week 7) is not part of Pilas; the vote endpoint already accepts
`transport_type: "hardware"`.

---

## 2. Architecture & Offline Design

* **Network Delivery**: Static pages served by the appliance over the isolated `TutorBox` AP; nginx in front publishes them on port 80 and lets phones' captive-portal probes open `/alumno/` automatically. Inside the phone's sign-in browser, `localStorage` (the login token) is sandboxed — opening the page later in the normal browser means logging in again.
* **Same origin**: no CORS, no API host configuration — pages use relative `/api/v1` URLs.
* **Hardware Agnostic**: Built to communicate via standard HTTP endpoints, seamlessly interoperating alongside physical ESP32 clickers.

---

## Next Steps

* **[REST API Specifications](../docs/api/README.md)**: Explore endpoint contracts for frontend client integration.
* **[Documentation Portal](../docs/README.md)**: View the overarching documentation index.
* **[10-Week Engineering Roadmap](../docs/milestones/roadmap.md)**: View frontend deliverables scheduled across Weeks 2–10.
