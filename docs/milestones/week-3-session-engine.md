# Week 3 Milestone: Session Engine, >51% Rule & Vote Persistence

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Docs** › **Milestones** › **Week 3 Milestone** • **Related:** [Engineering Roadmap](roadmap.md) • [Diagnostic Distractors](../architecture/diagnostic-distractors.md) • [Database Schema](../database-schema.md)

</div>

---

This document summarizes the technical deliverables, architectural implementations, and quality metrics achieved during the **Week 3 Milestone** by **Student B (Pilot)** and **Student A (Copilot)**.

---

## 1. Executive Summary & Verification Metrics
* **Theme**: *"From Button to Pedagogical Decision: Anatomy of a Quiz Turn"*
* **Status**: **Copilot (Student A) Complete & Green · Pilot (Student B) In Progress**
* **Backend Test Suite**: **589 / 589 passing tests** (70 new integration and unit tests added in Week 3 across persistence, aggregation, rule evaluation, lifecycle, and API layers).
* **Statement Coverage**: **100.00% coverage** across all 2,883 statements (`pyproject.toml` enforces `--cov-fail-under=80`).
* **Linter & Formatter**: **0 errors, 0 warnings** (`pre-commit run --all-files` clean across all 7 hooks).
* **Modularity Compliance**: **100% of source files $\le 150$ LoC** and **100% of test files $\le 300$ LoC** (enforced by Single Responsibility decomposition).
* **Key Milestone Artifacts**:
  * Idempotent migration `010_add_quiz_sessions_and_votes.sql` enforcing first-press locks via `UNIQUE(round_id, student_id)`.
  * Deterministic **>51% Rule** evaluator with formal validation across all 12 edge cases.
  * Monotonic countdown timer with simulated clock injection for deterministic TTL window expiration.
  * Versioned REST API endpoints (`/api/v1/session`) coordinating match creation, turn lifecycle, and student voting.

---

## 2. Implemented Subsystems by Lead

### A. Student A (Copilot): Real-Time Session Engine, >51% Rule, Persistence & REST API
1. **Database Persistence & First-Press Locking (`010_add_quiz_sessions_and_votes.sql`)**:
   * Migration `010_add_quiz_sessions_and_votes.sql` establishing tables `quiz_sessions`, `quiz_session_rounds`, and `quiz_session_votes` with indexing on `(session_id, round_index)`, `student_id`, and `(is_correct, misconception)`.
   * Strict database-layer first-press lock enforcement via `UNIQUE(round_id, student_id)`, preventing duplicate vote submissions per question round.
   * High-speed repository layer (`backend/src/db/session_repository.py`, `backend/src/db/round_repository.py`, `backend/src/db/vote_repository.py`, `backend/src/db/session_mapper.py`) supporting atomic vote insertions, round progression, and aggregate vote tallies.
2. **Domain Models & Exception Contracts (`backend/src/session/`)**:
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
     * `schema.py`: Pydantic request/response models for match creation, voting, and telemetry.
     * `routes_host.py`: Teacher endpoints for match creation (`POST /`) and turn progression (`/start`, `/close`, `/reveal`, `/next`).
     * `routes_participant.py`: Public state inspection (`GET /{session_id}`) and student vote submission (`POST /{session_id}/vote`) returning `409 Conflict` on duplicate submissions.
     * `routes_report.py`: Aggregate match reporting (`GET /{session_id}/report`) with accuracy calculations.
     * Registered in `backend/src/api/router.py`.

---

### B. Student B (Pilot): Device-Agnostic VoteTransport & Web Voting Client

**Interface Contracts & Open Hooks Provided by Student A for Student B Integration:**

* **Open Event Hook in `QuizSessionEngine`** (`backend/src/session/engine.py`):
  ```python
  EventListener = Callable[[str, dict[str, Any]], None]

  engine.add_event_listener(listener)
  ```
  * Dispatches events: `session_created`, `session_started`, `round_closed`, `round_revealed`, `round_advanced`, and `vote_cast`.
  * Student B binds web transport notifications or hardware clicker telemetry to this hook without modifying session business logic.

* **Voting Submission Contract** (`POST /api/v1/session/{session_id}/vote`):
  * Accepts `{"selected_option": "A"|"B"|"C"|"D", "transport_type": "web"|"hardware", "device_id": "...", "response_time_ms": 1200.0}`.
  * Returns `200 OK` with recorded vote details, or `409 Conflict` if the student or clicker has already voted in this round.

**Work Packages** *[In Progress / Student B to complete]*:

1. **Device-Agnostic `VoteTransport` Abstract Interface**:
   * Define the production `VoteTransport` interface abstracting web browser connections, ESP32 clicker radio frames, and testing harnesses.
2. **Mobile Web Voting Client (`pwa/quiz/student.html`)**:
   * Responsive A–D voting keypad optimized for student smartphones and tablets connected to the local classroom AP.
   * Real-time visual feedback indicating when the voting window is open, countdown remaining, and acknowledgment upon successful first-press lock.
3. **Teacher Management Portal (`pwa/quiz/host.html`)**:
   * Host UI to select topics, initiate quiz sessions, control turn progression (`Start`, `Close`, `Reveal`, `Next`), and inspect live turnout charts.
4. **Tuesday Jury Defense**: *"From Button to Pedagogical Decision: Anatomy of a Quiz Turn"*
   1. The lifecycle of a single vote from touch interface through transport abstraction to database persistence.
   2. Mathematical justification and edge cases of the >51% threshold for spoken distractor remediation.
   3. Architectural advantages of decoupling real-time session state from transport protocols.
