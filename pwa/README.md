# TutorBox Frontend (PWA)

Classroom web clients hosted directly on the NVIDIA Jetson Orin Nano appliance (both the vanilla HTML/JS reference client in `pilas/` and the modular React 19 + TypeScript PWA in `app/`).

<div align="center">

| 🏠 [TutorBox](../README.md) | 📚 [Docs](../docs/README.md) | ⚙️ [Backend](../backend/README.md) | 📱 **PWA** | 🔌 [Infra](../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Frontend (PWA) Hub** • **Related:** [Docs Hub](../docs/README.md) • [REST API Hub](../docs/api/README.md) • [Three Modes](../docs/architecture/three-modes.md)

</div>

---

## 1. Pilas — the classroom quiz client (`pilas/`)

Pilas is the shipped Classroom Quiz client: three vanilla HTML pages plus a shared `static/tb.js`,
served by the FastAPI backend itself (`backend/src/main.py` mounts the client directory per folder), so every
page talks to `/api/v1` on the same origin. There is no build step and no state of its own: the
backend session engine is the only source of truth and the pages poll it once per second.

| URL | Who | What it does |
| :--- | :--- | :--- |
| `/maestro/` | Teacher (role `teacher`/`admin`) | Login → pick a topic → number of questions → the local model writes every question (`POST /api/v1/quiz/generate`, no seed bank) → student roster → start the match → live count, close/reveal/next → group summary + CSV. When one wrong answer takes >51% of the class, the device reads the misconception explanation out loud (offline multi-tier TTS: Qwen3-TTS -> Sherpa -> Piper -> espeak-ng, Spanish). |
| `/alumno/` | Students | **Opens by itself when a phone joins the `TutorBox` Wi-Fi** ([captive portal](../infra/captive-portal.md)). Login or self-signup (forced PIN change when the teacher reset it) → auto-join the current match → A–D vote (first press locks) → result with the explanation for the chosen distractor → final score. |
| `/pantalla/` | HDMI classroom screen | Question + countdown + vote count, then the correct answer with the aggregate bars. Never per-student votes. |
| `/` | — | Redirects to `/alumno/` (to `http://tutorbox/alumno/` when reached through any other name). |

### Run it

```bash
sudo apt install espeak-ng                           # offline voice for the >51% intervention
cd backend
python -m uvicorn main:app --app-dir src --host 0.0.0.0        # teacher: http://<appliance-ip>:8000/maestro/
# classroom: nginx publishes the same process on :80 → http://tutorbox/maestro/ (infra/nginx/tutorbox.conf)
```

Bootstrap teacher: `teacher1` / `1234` (`SEED_TEACHER_*` in `.env`). The model must be reachable at
`SLM_BASE_URL`; when a generation fails the slot is skipped and the teacher is told — nothing is
served from the question bank.

### Endpoints used

| Endpoint | Page |
| :--- | :--- |
| `GET /health` | teacher login indicator |
| `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/users/me`, `PATCH /api/v1/users/me/pin` | all logins, session restore, forced PIN rotation |
| `POST /api/v1/users/signup` | student "Crear cuenta" |
| `GET /api/v1/staff/users`, `POST /api/v1/staff/users`, `POST /api/v1/staff/users/{id}/reset-pin` | teacher roster |
| `GET /api/v1/quiz/topics`, `POST /api/v1/quiz/generate` (`save_to_bank: true`), `GET /api/v1/quiz/generation-metrics` | topic cards, question generation, ETA |
| `POST /api/v1/session`, `/start`, `/close`, `/reveal`, `/next`, `GET /api/v1/session/{id}/report` | teacher match control |
| `GET /api/v1/session/{id}/speech?lang=es` | teacher device: offline multi-tier TTS (Qwen3-TTS -> Sherpa -> Piper -> espeak-ng) WAV read out loud when the >51% rule fires |
| `GET /api/v1/session/current`, `GET /api/v1/session/{id}` | students and screen (polling), teacher (own match) |
| `POST /api/v1/session/{id}/vote` | student vote |

Client-side only (per browser `localStorage`): the bearer token, the teacher's current session id and
per-round reveal history (for the summary page), and each student's own votes/score. The ESP32
clicker transport (Week 7) is not part of Pilas; the vote endpoint already accepts
`transport_type: "hardware"`.

---

## 2. React PWA — Modern Modular Classroom Client (`pwa/app/`)

`pwa/app/` is the modular, type-safe React 19 + TypeScript + Vite Progressive Web Application designed under Feature-Sliced Design (FSD). It maintains strict 1-to-1 feature parity with `pilas/` while eliminating monolithic code and providing automated test coverage.

### Directory Structure & FSD Architecture

```
pwa/
├── pilas/                  # Reference classroom client (vanilla HTML/JS)
├── app/                    # Modern classroom client (React 19 + TypeScript + Vite FSD)
│   ├── index.html          # SPA HTML template
│   ├── package.json        # Dependencies & scripts (React 19, TypeScript, Vite, Vitest)
│   ├── tsconfig.json       # Strict TypeScript compiler options
│   ├── vite.config.ts      # Multi-route distribution plugin (.cache/pwa/dist)
│   ├── vitest.config.ts    # Component & logic test runner configuration
│   └── src/
│       ├── main.tsx        # Application mount entry point
│       ├── app/            # Global application layer
│       │   ├── App.tsx             # Route selector (/alumno, /maestro, /pantalla)
│       │   ├── ErrorBoundary.tsx   # Top-level fault isolation boundary
│       │   └── styles/             # CSS design tokens & animations
│       ├── pages/          # Role-based page views
│       │   ├── student/            # Student mobile voting interface (/alumno/)
│       │   ├── teacher/            # Teacher control console (/maestro/)
│       │   └── display/            # Projector display view (/pantalla/)
│       ├── features/       # Isolated domain feature slices
│       │   ├── auth/               # Login form, PIN reset modal, auth hook
│       │   ├── session-engine/     # Round state machine & polling coordinator
│       │   ├── voting/             # Voting grid, response latency & first-press lock
│       │   ├── roster/             # Student management & PIN resets
│       │   ├── question-generator/ # Topic selector & question count picker
│       │   ├── speech/             # TTS audio playback & status badge
│       │   └── match-report/       # Aggregate analytics, remediation alert & CSV export
│       ├── shared/         # Cross-cutting primitives & design system
│       │   ├── api/                # Type-safe fetch client & endpoint contracts
│       │   ├── lib/                # Storage & audio synthesis helpers
│       │   └── ui/                 # Reusable accessible UI components
│       └── test/           # Vitest environment mocks & setup
└── README.md
```

### Serving via Backend

The backend (`backend/src/main.py`) serves the React PWA build output (`.cache/pwa/dist`)
by default and supports runtime selection of the frontend directory via the `PWA_STATIC_DIR`
environment variable:

```bash
# Default: serves .cache/pwa/dist (built from pwa/app; fails fast if never built)
python -m uvicorn main:app --app-dir backend/src

# Legacy fallback: serve the vanilla reference client explicitly:
export PWA_STATIC_DIR="pwa/pilas"
python -m uvicorn main:app --app-dir backend/src
```

### Development & Build Commands

Inside `pwa/app/`:

```bash
pnpm dev        # Launch Vite development server on port 5173 with API proxying
pnpm typecheck  # Strict TypeScript verification (0 errors)
pnpm test       # Execute Vitest test suite (13 suites, 49 tests)
pnpm build      # Build production bundle to dist/
```

---

### Classroom mode

`src/features/mode/` lets the teacher pick the class mode (quiz, tutor, take-home) from `/maestro/`;
`/pantalla/` and `/alumno/` poll it and follow. See [Three Modes §4](../docs/architecture/three-modes.md#4-choosing-the-mode).

---

## <a id="3-tareas--take-home-math-apps-tareas"></a>3. Tareas — take-home math apps (`tareas/`)

Grade-specific math apps that students also take home. Unlike `pilas/` and `app/` they need no
backend: plain static files, no build step.

| Path | Served at | What it is |
| :--- | :--- | :--- |
| [`tareas/primero/`](tareas/primero/README.md) | `/tareas/primero/` | "Aprende Matemáticas con Q'uq'" — 1st-grade (Primero) CNB math, vanilla JS + Canvas. Played in the classroom browser. |
| [`tareas/android/`](tareas/android/README.md) | — | Android wrapper that packs `primero/public` into an offline APK (`gradlew publishApk`). |
| `tareas/descargas/` | `/descargas/` | Family download page with install steps (Spanish) plus `primero.apk`. |
| `tareas/cnb/` | — | CNB curriculum sources (MINEDUC PDFs/Word, grades 1–5) the lessons are aligned to. |

**Why an APK and not an installable PWA:** browsers only run service workers (offline support) and
offer "Install app" on HTTPS pages, and the offline Jetson serves plain `http://tutorbox`. The APK
carries every file inside and speaks through the phone's own offline text-to-speech, so it keeps
working at home with no internet. Android only; iPhones can still play in the classroom browser.
Chrome warns *"no se puede descargar de forma segura"* on any APK over HTTP — families tap
**Conservar**; the download page says so.

Both mounts are listed in `REPO_MOUNTS` (`backend/src/main.py`) and exempt from captive-portal
redirects (`RESERVED_PREFIXES`, `backend/src/api/captive.py`).

---

## 4. Architecture & Offline Design

* **Network Delivery**: Static pages served by the appliance over the isolated `TutorBox` AP; nginx in front publishes them on port 80 and lets phones' captive-portal probes open `/alumno/` automatically. Inside the phone's sign-in browser, `localStorage` (the login token) is sandboxed — opening the page later in the normal browser means logging in again.
* **Same origin**: no CORS, no API host configuration — pages use relative `/api/v1` URLs.
* **Hardware Agnostic**: Built to communicate via standard HTTP endpoints, seamlessly interoperating alongside physical ESP32 clickers.

---

## Next Steps

* **[REST API Specifications](../docs/api/README.md)**: Explore endpoint contracts for frontend client integration.
* **[Documentation Portal](../docs/README.md)**: View the overarching documentation index.
* **[10-Week Engineering Roadmap](../docs/milestones/roadmap.md)**: View frontend deliverables scheduled across Weeks 2–10.
