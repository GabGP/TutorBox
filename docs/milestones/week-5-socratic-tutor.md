# Week 5 Milestone: Socratic Tutor Mode

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Milestones](roadmap.md) › **Week 5 Milestone** • **Related:** [Engineering Roadmap](roadmap.md) • [Socratic Pedagogy](../architecture/socratic-pedagogy.md) • [Tutor API Reference](../api/tutor.md) • [Dialogue Telemetry](../database/dialogue.md)

</div>

---

This document summarizes the technical deliverables, architectural implementations, and quality metrics achieved during the **Week 5 Milestone** by **Student A (Copilot: Socratic Engine, SymPy Containment & Problem Bank)** and **Student B (Pilot: Installable Offline Tutor Client & Dialogue Telemetry)**.

---

## 1. Executive Summary & Verification Metrics

* **Theme**: *"Socratic Tutoring with Mechanical Guarantees"*
* **Status**: **Copilot (Student A) Complete & Green · Pilot (Student B) Complete & Green**
* **Backend Test Suite**: **1793 / 1793 passing tests** (748 of them cover the tutor: `tests/modes/socratic/`, `tests/api/tutor/`, the turn-log repository and the tutor settings).
* **Statement Coverage**: **100.00% statement coverage** across all 6,379 source statements (`pyproject.toml` enforces `--cov-fail-under=100`).
* **Frontend Test Suite**: **299 / 299 passing tests** across 57 Vitest files, with `tsc -b --noEmit` reporting 0 errors.
* **Linter & Formatter**: **0 errors, 0 warnings** (`pre-commit run --all-files` clean across all 7 hooks).
* **Modularity Compliance**: **100% of production source files $\le 150$ LoC** and **100% of test files $\le 300$ LoC**, strictly validated by `tests/test_modularity_policy.py` (largest tutor module: `modes/socratic/problems.py`, 150 lines).
* **Acceptance Criteria Status**:
  * ✅ **30 dialogue turns, 10 adversarial probes, 0 solution leaks**: `test_containment_dialogues.py::test_thirty_turns_ten_probes_and_no_solution_before_the_child_finds_it`.
  * ✅ **Problem bank of $\ge 40$ validated questions in CI**: 48 labeled problems, each proven by SymPy in `test_problem_bank.py`.
  * ✅ **PWA tutor added to the home screen and functioning on the classroom network without internet**: amended from "installed and functioning offline on 3 test devices" (Section 2.B, item 7). Observed on one iPhone on 2026-10-08: the tutor opens from its home-screen icon and the login is kept between launches. No Android phone was available.
* **Key Milestone Artifacts**:
  * **Deterministic Dialogue State Machine**: `planner.py` chooses every pedagogical move without the model and climbs a bounded 4-tier hint ladder ($0 \to 3$).
  * **SymPy Containment Guardrail**: `containment.py` blocks any reply that states an accepted answer in digits, in Spanish words, or as an expression SymPy evaluates to it.
  * **Labeled Problem Bank**: 48 problems for 1.º–5.º primaria, labeled with the quiz's `CURRICULUM_TAXONOMY` topic and subconcept and with the CNB grade and topic.
  * **Dialogue Turn Telemetry**: every turn in `turn_logs` carries the concept practised (quiz taxonomy pair and CNB topic), the scaffolding strategy applied and, on a wrong answer, the misconception behind it.
  * **Tutor REST API**: 4 endpoints under `/api/v1/tutor` with a per-login turn gate and a live roster for the teacher.
  * **Classroom Chat Client**: text-only tutor chat on `/alumno/` and a live student panel on `/maestro/`, both following the class mode the teacher picks.

---

## 2. Implemented Subsystems by Lead

### A. Student A (Copilot Scope: Socratic Engine, SymPy Containment & Problem Bank)

1. **Dialogue State Machine & 4-Tier Hint Ladder (`backend/src/modes/socratic/`)**:
   * `planner.py` turns each message and the stored `Conversation` (problem in progress and hint level) into the next move.
   * A new problem starts at level 0; every wrong answer or request for help sets `min(level + 1, 3)`, so the ladder stops at level 3 and repeats it until the child solves the problem.
   * Hint texts per level: restate the goal (0), the concept (1), a smaller step (2), a worked example with other numbers (3). Operations live in `operation_hints.py` and `hints.py`; equations in `equation_hints.py`, where level 2 names the first step to undo and level 3 solves a parallel equation.
   * `state.py` keeps conversations in a thread-safe, size-bounded in-memory store (500 entries, least recently used dropped) keyed by the login session.
2. **SymPy Containment Guardrail (`containment.py`, `guard.py`)**:
   * Until the child finds the answer, no reply may state it outside the problem itself: digits (`68`, `136/2`, `68.0`), Spanish words (`sesenta y ocho`), or an expression or assignment that SymPy evaluates to it (`x = 12 - 5`).
   * A model rewording may not add any number or calculation the hint did not have, so the model cannot compute for the child.
   * Every deterministic hint passes the same check before use. A failing model reply is discarded, the turn records `containment_triggered`, and the child receives the deterministic hint.
3. **Bounded Mathematics (`backend/src/core/math_engine/`)**:
   * `exact_arithmetic.py` evaluates operations on exact fractions with `+ − × ÷` only, so no message can make the backend compute without end.
   * `safe_parser.py` reads equations and never accepts a power of a power; expressions over 60 characters and numbers over $10^9$ are not evaluated.
4. **Model Voice Behind a Gateway (`gateway.py`, `prompts.py`, `text.py`)**:
   * `DeepSeek-R1-Distill-Qwen-1.5B` (Q8_0, ~1.9 GB) only rewords the chosen hint or explains a CNB concept in two sentences.
   * At most 2 replies are generated at once (`TUTOR_MAX_CONCURRENT`); other turns wait up to 20 s and then receive the deterministic hint.
   * Output cleaning strips reasoning, LaTeX and Markdown; replies with English, other scripts, role-play labels or more than 320 characters are rejected.
5. **Input & Curriculum Scope Guards (`input_guard.py`, `curriculum.py`, `cnb_matematicas.json`)**:
   * Text only: data URIs, image tags, Markdown images and base64 blobs are refused.
   * Topics are limited to the CNB mathematics of 1.º–5.º primaria; later-grade math and non-math questions are refused with a pointer to what the tutor can do.
6. **Labeled Problem Bank (`problem_bank.json`, `bank.py`)**:
   * 48 problems: 24 arithmetic (+ − × ÷) and 24 pre-algebra (12 one-step and 12 two-step equations).
   * `test_problem_bank.py` proves every answer with SymPy, checks each structure with the quiz validators, and walks every problem through four distinct, leak-free hints and the $0 \to 3$ climb.
7. **Tutor REST API (`backend/src/api/tutor/`)**:
   * `POST /api/v1/tutor/message`, `POST /api/v1/tutor/reset`, `POST /api/v1/tutor/ping` and `GET /api/v1/tutor/students`, protected by role.
   * `gate.py`: one turn at a time per login and 12 turns per minute (`429` otherwise). The chat answers `409` outside `tutor` mode.
   * `roster.py`: in-memory teacher panel; a student counts as connected for 45 s after a ping and is listed for 30 minutes.
8. **Baseline Turn Logging (`backend/src/core/db/turn_log_repository.py`)**:
   * One `turn_logs` row per turn: the child's text, the SymPy expression and target, correctness, the raw model output, the containment flag, the final reply and the hint level.
9. **Classroom Chat Client (`pwa/app/src/features/tutor/`)** (delivered together with the engine):
   * `TutorChat.tsx` and `useTutorChat.ts`: text-only chat that refuses pasted or dropped files, pings every 20 s, and keeps the conversation in `sessionStorage` for the current tab.
   * `TutorRoster.tsx` and `useTutorRoster.ts`: the teacher's live list of students, problem in progress and hint level.
   * `tutorApi.ts`: typed API client contract for the four endpoints.
   * `StudentView.tsx` shows the login form and then the chat while the class mode is `tutor`.

---

### B. Student B (Pilot Scope: Installable Offline Tutor Client & Dialogue Telemetry)

**Baseline Already in Place (Student B, Weeks 3–4):**

* **Student Login (`pwa/app/src/features/auth/`)**: login, self-signup and forced PIN change; the Bearer token is kept in `localStorage` and `useAuth` restores the session on every visit.
* **Install Metadata (`pwa/app/index.html`, `public/static/manifest.webmanifest`)**: `display: standalone`, `start_url: /alumno/`, theme color and 192/512 SVG icons, verified by `pwaMeta.test.ts`.

**Interface Contracts Provided by Student A for Student B Extension:**

* **`TurnResult`** (`backend/src/modes/socratic/engine.py`):
  ```python
  @dataclass(frozen=True)
  class TurnResult:
      reply: str
      kind: str
      hint_level: int
      used_model: bool
      containment_triggered: bool
      llm_raw: str | None
      problem: Problem | None
      is_correct: bool | None
      topic_id: str | None
      attempt: Fraction | None = None
  ```
  * `kind` names the move (`hint`, `praise`, `explain`, `think`, `idea`, `word_problem`, `social`, `input`, `beyond`, `negative`, `off_topic`, `orphan`, `show_work`); `hint_level` is the ladder tier applied; `topic_id` is the CNB topic when one was explained; `attempt` is the value the child typed when an answer was judged, added this week for the error-type classifier.
* **`TurnRecord` / `record_turn`** (`backend/src/core/db/turn_log_repository.py`): the single write path into `turn_logs`, called once per turn from `api/tutor/turn_logging.py`.
* **Concept Labels** (`backend/src/modes/socratic/bank.py`): every bank problem carries the quiz's `CURRICULUM_TAXONOMY` topic and subconcept, the vocabulary the weekly report uses.
* **`ConversationStore`** (`backend/src/modes/socratic/state.py`): `get`, `put` and `drop` by key. The key today is the login session id.

**Delivered Subsystems:**

1. **Telemetry Storage Contract (`backend/migrations/012_add_turn_log_pedagogy.sql`, `backend/src/core/db/turn_log_repository.py`)**:
   * Five nullable `TEXT` columns on `turn_logs` (`concept_topic`, `concept_subconcept`, `cnb_topic`, `error_type`, `scaffolding_strategy`) and the index `idx_turn_logs_concept`.
   * No `CHECK` constraints: the vocabularies live in code and tests ([Dialogue Telemetry §2.1](../database/dialogue.md#21-telemetry-label-vocabularies)), so the taxonomy can grow without a migration.
2. **Concept Mapper (`backend/src/modes/socratic/telemetry/concept.py`)**:
   * Maps the problem's operation to the quiz's `CURRICULUM_TAXONOMY` topic and subconcept and to its CNB topic. A concept question keeps its CNB topic even where the quiz taxonomy has no entry (geometry, time, money).
   * All 48 problems of Student A's bank derive to the labels of their bank entry (`test_concept.py`).
3. **Scaffolding Strategy Mapper (`telemetry/strategy.py`)**:
   * Names what the tutor did: the four ladder rungs (`restate_goal`, `concept_clue`, `smaller_step`, `worked_example`), eight other strategies, and `other` for a move not named yet.
   * A test scans `planner.py` for every move kind, so a new kind cannot go unnamed.
4. **Error-Type Classifier (`telemetry/error_type.py`, `telemetry/error_rules_*.py`)**:
   * Each rule predicts the value a child would type after one specific mistake. The first prediction equal to the answer names the error with a quiz-taxonomy misconception slug; otherwise the turn is `unclassified`.
   * 16 slugs across addition and subtraction, times tables, division, order of operations, one- and two-step equations, percentages and fraction sums. Example: `2x + 4 = 14` answered with `10` is `forgot_division`.
   * Reads the judged value from the new `attempt` field on `Move` and `TurnResult` (three lines each in Student A's `planner.py` and `engine.py`).
5. **Wiring (`backend/src/api/tutor/turn_logging.py`)**:
   * `build_turn_record` is pure and `log_turn` stores it. The labels come from the move the engine already chose, never from the model's text, and never change a reply.
   * `test_turn_logging.py` drives a six-turn dialogue through `POST /api/v1/tutor/message` and reads the five columns back; `test_label_consistency.py` proves every misconception belongs to the concept of its problem.
6. **Parser Corrections Found While Testing Telemetry (`backend/src/modes/socratic/problems.py`, Student A's module)**:
   * An operator next to a parenthesis was dropped (`(2 + 3) por 4` was read as `(2 + 3)`), and a leading minus on an equation was lost (`-3 + x = 5` was solved as 2). Both are fixed in place.
   * The containment guard shares the normalizer, so it now also blocks a reply such as `(14 - 4) entre 2` that works out the answer.

7. **Home-Screen Installation & Device Evidence ([PWA README](../../pwa/README.md#tutor-on-the-home-screen))**:
   * Design decision (Pilot): the tutor gets no service worker and no install wrapper. Browsers run service workers and offer installation only in a secure context (HTTPS or `localhost`), and the appliance serves plain `http://tutorbox` ([PWA README §3](../../pwa/README.md#3-tareas--take-home-math-apps-tareas), [Captive Portal §6](../../infra/captive-portal.md#6-limitations--field-notes)). Every tutor reply also needs the appliance (the model and SymPy run there), so a copy installed for use away from the classroom would have nothing to do. The client students keep at home is the take-home app in `pwa/tareas/`, already installable offline as an Android APK.
   * Amended acceptance criterion: the tutor is added to the phone's home screen and works on the classroom network without internet.
   * Observed on one iPhone on 2026-10-08 (Safari → Share → *Add to Home Screen*, backend in `tutor` mode on the local network): iOS asks to confirm opening the page because it is not HTTPS, then the tutor opens and works, and the login is still there on the next launch.
   * Limits observed on the same device: closing the app completely, or a long time in the background, clears the visible conversation (`sessionStorage` ends with the app). With no connection to the appliance the icon shows nothing, because the page itself loads from the appliance; showing it offline needs a service worker, and therefore HTTPS. No Android phone was available.

**Session State (kept as delivered):**

* The login persists across visits within a school day: the Bearer token stays in `localStorage` and the session expires 12 hours after login (`SESSION_TTL_HOURS`). Until then the server keeps the problem in progress and the hint level under that same login session, unless the backend restarts.
* The visible chat history is kept in `sessionStorage` for the current tab, the scope Student A chose for the captive-portal sign-in window. No change is planned.

---

## 3. Tuesday Jury Defense Package (Copilot A Defense Script)

* **Topic**: *"Socratic Tutoring with Mechanical Guarantees"*
* **Presenter**: Student A (Copilot)

### Key Talking Points for the Jury:

1. **Why the Tutor Never Reveals Answers, and Why a Prompt Is Not Enough**:
   * Measured on the Jetson, the 1.5B model asked to tutor freely invents dialogue turns and states the answer; asked to reword a given hint it stays close to it.
   * The pedagogy is therefore deterministic, and the model only supplies wording. SymPy containment checks every reply, the deterministic hints included.
2. **Deterministic Hint Escalation Ladder & Termination Bounds**:
   * Levels $0 \to 3$ with `min(level + 1, 3)`: the ladder cannot run past level 3, and solving the problem resets it.
   * Load bounds: 2 concurrent generations, a 20 s queue, one turn at a time per login and 12 turns per minute.
3. **Architectural Differences Between Quiz Mode and Tutor Mode**:
   * Quiz: one question for the whole class, votes aggregated by the >51% rule, the model generates questions before the match.
   * Tutor: one conversation per student, state per login, the model rewords during the turn and a guard decides whether its text is shown.
4. **Evidence in CI**:
   * `test_containment_dialogues.py`: 30 turns in which a complying model answers 10 "dame la respuesta" probes, each in another form; all 10 are contained.
   * `test_problem_bank.py`: 48 problems proven by SymPy and walked through the full ladder.
