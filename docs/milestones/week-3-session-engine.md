# Week 3 Milestone: Session Engine, >51% Rule & Vote Persistence

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Milestones](roadmap.md) › **Week 3 Milestone** • **Related:** [Engineering Roadmap](roadmap.md) • [Diagnostic Distractors](../architecture/diagnostic-distractors.md) • [Database Schema](../database/README.md)

</div>

---

This document summarizes the technical deliverables, architectural implementations, and quality metrics achieved during the **Week 3 Milestone** by **Student B (Pilot)** and **Student A (Copilot)**.

---

## 1. Executive Summary & Verification Metrics
* **Theme**: *"From Button to Pedagogical Decision: Anatomy of a Quiz Turn"*
* **Status**: **Week 3 Milestone Complete & Green**
* **Backend Test Suite**: **693 / 693 passing tests** (174 new integration, unit, speech, captive, and concurrency tests added across persistence, aggregation, rule evaluation, lifecycle, schema contracts, event dispatching, public phase-gated state, concurrent load, offline TTS, audio caching, and captive portal).
* **Statement Coverage**: **100.00% coverage** across all 3,281 statements (`pyproject.toml` enforces `--cov-fail-under=80`).
* **Linter & Formatter**: **0 errors, 0 warnings** (`pre-commit run --all-files` clean across all 7 hooks).
* **Modularity Compliance**: **100% of source files $\le 146$ LoC** (Week 3 session modules $\le 139$ LoC, well under the $\le 150$ LoC hard ceiling) and **100% of test files $\le 299$ LoC** (well under the $\le 300$ LoC ceiling), verified by `test_modularity_policy.py`.
* **Key Milestone Artifacts**:
  * Idempotent migration `010_add_quiz_sessions_and_votes.sql` enforcing first-press locks via `UNIQUE(round_id, student_id)`.
  * Deterministic **>51% Rule** evaluator with formal validation across all 12 edge cases.
  * Monotonic countdown timer with simulated clock injection for deterministic TTL window expiration.
  * Versioned REST API endpoints (`/api/v1/session`) coordinating match creation, turn lifecycle, and student voting.
  * Concurrency verification suite (`backend/tests/api/session/test_session_concurrency.py`) proving 15 simultaneous clients (web + hardware), 0 lost votes, and first-press lock race resolution.
  * Public phase-gating (`state_builder.py`) hiding question answers during active voting and dynamically publishing diagnostic explanations upon reveal.
  * Offline TTS speech synthesis pipeline (`backend/src/api/session/speech.py`, `backend/src/core/tts/espeak.py`) generating WAV audio for >51% distractor remediation.
  * Captive portal subsystem (`backend/src/api/captive.py`, `infra/captive-portal.md`) providing zero-configuration classroom discovery.
  * Event dispatcher (`session/events.py`) and entity resolver (`api/session/dependencies.py`) maintaining strict Single Responsibility decoupling.

---

## 2. Implemented Subsystems by Lead

### A. Student A (Copilot): Real-Time Session Engine, >51% Rule, Persistence & REST API
1. **Database Persistence & First-Press Locking (`010_add_quiz_sessions_and_votes.sql`)**:
   * Migration `010_add_quiz_sessions_and_votes.sql` establishing tables `quiz_sessions`, `quiz_session_rounds`, and `quiz_session_votes` with indexing on `(session_id, round_index)`, `student_id`, and `(is_correct, misconception)`.
   * Strict database-layer first-press lock enforcement via `UNIQUE(round_id, student_id)`, preventing duplicate vote submissions per question round.
   * High-speed repository layer (`backend/src/core/db/session_repository.py`, `backend/src/core/db/round_repository.py`, `backend/src/core/db/vote_repository.py`, `backend/src/core/db/session_mapper.py`) supporting atomic vote insertions, round progression, and aggregate vote tallies.
2. **Domain Models & Exception Contracts (`backend/src/modes/quiz/session/`)**:
   * Strongly typed domain models (`models.py`) defining `SessionStatus`, `RoundStatus`, `StudentVoteRecord`, `RoundTally`, `TurnDecision`, and `SessionSummary`.
   * Standardized exception hierarchy (`exceptions.py`) handling `SessionNotFoundError`, `RoundNotFoundError`, `InvalidSessionStateError`, `InvalidRoundStateError`, `VoteAlreadyCastError`, and `InvalidOptionError`.
3. **Vote Aggregator & Formal >51% Rule Evaluator**:
   * Distribution calculator (`aggregator.py`) tallying option frequencies (`A`, `B`, `C`, `D`), turnout count, participation rate, and identifying top chosen distractors.
   * Formal pedagogical decision engine (`evaluator.py`) implementing the strict inequality:
     $$\text{trigger\_audio} \iff \exists d \in \text{Distractors} : \frac{\text{votes}(d)}{\text{total\_votes}} > 0.51$$
   * Rigorous verification of all edge cases: exact 51.0% (silent), 50/50 splits (silent), distractor ties (silent), dispersed wrong answers (silent), majority correct (silent), and zero votes/timeout (silent).
4. **State Machine, Countdown Timer & Engine Coordinator**:
   * Monotonic countdown timer (`timer.py`) decoupled from wall-clock time with injectable time functions for testing.
   * Modular lifecycle decomposition:
     * `session_manager.py`: Session initialization and state querying.
     * `turn_manager.py`: Round opening, window closure, reveal outcome, and round advancement.
     * `vote_processor.py`: Vote validation, misconception mapping, first-press lock validation, and persistence.
     * `engine.py`: Unified coordinator providing open event listener hooks (`add_event_listener`) for downstream telemetry and transport binding.
5. **FastAPI Versioned REST Endpoints (`/api/v1/session`)**:
   * Modular route packages:
     * `schemas.py`: Pydantic request/response models for match creation, voting, and telemetry.
     * `host.py`: Teacher endpoints for match creation (`POST /`) and turn progression (`/start`, `/close`, `/reveal`, `/next`).
     * `participant.py`: Public state inspection (`GET /{session_id}`) and student vote submission (`POST /{session_id}/vote`) returning `409 Conflict` on duplicate submissions.
     * `reports.py`: Aggregate match reporting (`GET /{session_id}/report`) with accuracy calculations.
     * Registered in `backend/src/api/router.py`.
6. **Architectural Hardening & Modularity Decompression**:
   * Extracted `modes/quiz/session/events.py` (35 LoC) to encapsulate event dispatching and shared in-memory timer/listener state, decompressing `modes/quiz/session/engine.py` from 148 to 139 LoC.
   * Extracted `api/session/dependencies.py` (30 LoC) to centralize session and round entity resolution, reducing `api/session/host.py` from 149 to 130 LoC.
   * Extracted `modes/quiz/validation/similarity_helpers.py` (44 LoC) to isolate text normalization and string distance math, reducing `modes/quiz/validation/deduplication.py` from 148 to 114 LoC.
   * Standardized `api/staff/` action modules (`user_delete.py`, `user_recover.py`, `user_reset_pin.py`) and centralized DTO schemas across all API packages, establishing 100% compliance with $\le 146$ LoC across all production modules (well below the $\le 150$ LoC ceiling).
7. **Phase-Gated Public State & 15-Client Concurrency Verification Suite**:
   * Answer-Safe Public State (`api/session/state_builder.py`): Dynamic phase-gating for `GET /api/v1/session/current` and `GET /api/v1/session/{id}`, masking `correct_option` and distractor explanations during active voting while dynamically projecting aggregate counts and diagnostic explanations upon turn reveal.
   * Concurrency Verification Suite (`backend/tests/api/session/test_session_concurrency.py`, 273 LoC): Simulated live 5-question match with 15 simultaneous clients (10 web PWA + 5 ESP32 clickers) casting 75 total votes, proving 100% first-press lock enforcement, 0 lost votes, and immediate race condition resolution under concurrent load.

---

### B. Student B (Pilot): Device-Agnostic VoteTransport & Web Voting Client

**Interface Contracts & Open Hooks Provided by Student A for Student B Integration:**

* **Open Event Hook in `QuizSessionEngine`** (`backend/src/modes/quiz/session/engine.py`):
  ```python
  EventListener = Callable[[str, dict[str, Any]], None]

  engine.add_event_listener(listener)
  ```
  * Dispatches events: `session_created`, `session_started`, `round_closed`, `round_revealed`, `round_advanced`, and `vote_cast`.
  * Student B binds web transport notifications or hardware clicker telemetry to this hook without modifying session business logic.

* **Voting Submission Contract** (`POST /api/v1/session/{session_id}/vote`):
  * Accepts `{"selected_option": "A"|"B"|"C"|"D", "transport_type": "web"|"hardware", "device_id": "...", "response_time_ms": 1200.0}`.
  * Returns `200 OK` with recorded vote details, or `409 Conflict` if the student or clicker has already voted in this round.

**Work Packages & Architectural Deliverables:**

1. **Architectural Decision: Wire Protocol Seam over In-Process `VoteTransport`**:
   * *Architectural Evolution*: Early planning envisioned an in-process Python class hierarchy (`VoteTransport` OOP interface). However, distributed heterogeneous clients (ESP32 microcontrollers running embedded C++ and student smartphones running JavaScript PWA) operate over physical network boundaries and cannot share an in-memory Python runtime.
   * *The Wire Protocol Seam*: The **HTTP REST API contract (`POST /api/v1/session/{id}/vote`)** serves as the true hardware-agnostic transport layer. The engine ingests votes identically regardless of whether the source is `transport_type: "web"` or `"hardware"`.
   * *Verification*: Automated 15-client concurrency test match (`backend/tests/api/session/test_session_concurrency.py`) proving 100% first-press lock enforcement and **0 lost votes** across 5 rounds with 75 total votes under simultaneous mixed web and hardware traffic.
2. **Mobile Web Voting Client (`pwa/pilas/alumno/index.html`)**:
   * Delivered responsive A–D voting keypad served directly by FastAPI.
   * Features real-time state synchronization via `/api/v1/session/current`, first-press locking upon selection, and post-reveal distractor explanation feedback.
3. **Teacher Management Portal & Screen (`pwa/pilas/maestro/` & `pantalla/`)**:
   * Delivered teacher console for session creation, real-time turnout monitoring, and turn progression controls (`Start`, `Close`, `Reveal`, `Next`).
   * Delivered dedicated HDMI screen interface (`pantalla/index.html`) presenting answer-safe countdowns and aggregate bar distributions without individual student identities.
4. **ESP32 Hardware Protocol Specification (`docs/architecture/esp32-protocol.md`)**:
   * Authored comprehensive 537-line engineering specification detailing BLE GATT provisioning, HTTP polling loops, token auth lifecycle, and network capacity planning for Week 7.
5. **Spoken Remediation Voice Integration (`pwa/pilas/maestro/` & Speech API)**:
   * Connected teacher portal to `GET /api/v1/session/{session_id}/speech?lang=es|quc` with audio streaming via offline eSpeak-ng engine (`backend/src/core/tts/espeak.py`).
   * Implemented iOS silent-WAV audio context priming, real-time speech indicator state (`loading`, `playing`, `done`, `error`), and bilingual toggle (Spanish vs K'iche').
6. **Captive Portal Architecture & Offline DNS (`backend/src/api/captive.py` & `infra/captive-portal.md`)**:
   * Implemented RFC 8952 captive portal API and OS detection probe handlers (`/generate_204`, `/hotspot-detect.html`, `/ncsi.txt`) with Nginx redirection to `/alumno/`.
7. **Tuesday Jury Defense (Presented by Copilot A)**: *"From Button to Pedagogical Decision: Anatomy of a Quiz Turn"*
   1. Data flow of a single vote from client touch/hardware button through the Wire Protocol to database persistence with first-press locking.
   2. Mathematical justification and formal edge cases of the >51% threshold for spoken distractor remediation.
   3. Architectural benefits of the Wire Protocol abstraction, proven via the 15-client concurrency test with zero lost votes.
