# Mode 1: Classroom Quiz & Real-Time Sessions Schema

Technical specification for question bank storage, SLM generation telemetry, live match sessions, voting windows, and student votes in **TutorBox**.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Database](README.md) › **Quiz Schema** • **Related:** [Core Schema](core.md) • [Migrations](migrations.md) • [Sessions API](../api/sessions.md)

</div>

---

## Table of Contents
- [1. Question Bank & AI Telemetry](#1-question-bank--ai-telemetry)
  - [Table: `quiz_questions`](#table-quiz_questions)
  - [Table: `quiz_generation_logs`](#table-quiz_generation_logs)
- [2. Match Sessions & Real-Time Voting](#2-match-sessions--real-time-voting)
  - [Table: `quiz_sessions`](#table-quiz_sessions)
  - [Table: `quiz_session_rounds`](#table-quiz_session_rounds)
  - [Table: `quiz_session_votes`](#table-quiz_session_votes)
- [3. Integrity & Concurrency Invariants](#3-integrity--concurrency-invariants)
  - [A. First-Press Locking Enforcement](#a-first-press-locking-enforcement)
  - [B. Question Soft-Deletion & Telemetry Integrity](#b-question-soft-deletion--telemetry-integrity)
- [Related Specifications](#related-specifications)

---

## <a id="1-question-bank--ai-telemetry"></a>1. Question Bank & AI Telemetry

### Table: `quiz_questions`
Question bank repository storing generated, seeded, and teacher-authored diagnostic quiz questions.

| Column | Type | Constraints | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `TEXT` | `PRIMARY KEY` | — | Unique question identifier (e.g., `'q_math_001'`, `'q_a1b2c3d4e5f6'`). |
| `topic` | `TEXT` | `NOT NULL` | — | Primary mathematics curriculum topic slug (e.g., `'arithmetic_integers'`, `'fractions'`). |
| `subconcept` | `TEXT` | `NOT NULL` | — | Granular curriculum subconcept slug (e.g., `'order_of_operations'`, `'simplification'`). |
| `question_text` | `TEXT` | `NOT NULL` | — | Natural language question statement in Spanish. |
| `options_json` | `TEXT` | `NOT NULL` | — | JSON-serialized dictionary of 4 choices: `{"A": "...", "B": "...", "C": "...", "D": "..."}`. |
| `correct_option`| `TEXT` | `NOT NULL`, `CHECK(correct_option IN ('A', 'B', 'C', 'D'))` | — | The single mathematically true option key. |
| `distractors_json`| `TEXT` | `NOT NULL` | — | JSON-serialized dictionary mapping the 3 incorrect options to diagnostic `misconception` and `explanation`. |
| `sympy_verified`| `INTEGER` | `NOT NULL`, `CHECK(sympy_verified IN (0, 1))` | `0` | `1` if mathematically proven and verified by SymPy, `0` otherwise. |
| `source` | `TEXT` | `NOT NULL`, `CHECK(source IN ('llm', 'seed', 'teacher'))` | `'llm'` | Provenance of the question record. |
| `created_at` | `TIMESTAMP` | — | `CURRENT_TIMESTAMP` | UTC timestamp of question insertion. |
| `deleted_at` | `TIMESTAMP` | `NULL` | `NULL` | Timestamp of soft-deletion (`NULL` for active questions). |

---

### Table: `quiz_generation_logs`
Dedicated telemetry trail capturing model identifiers, latency, retry counts, and rejection histories for every on-demand quiz generation request.

| Column | Type | Constraints | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | — | Unique generation log identifier. |
| `question_id` | `TEXT` | `NULL`, `FOREIGN KEY -> quiz_questions(id) ON DELETE SET NULL` | `NULL` | Foreign key referencing generated question if persisted (`NULL` for transient generations or failures). |
| `user_id` | `INTEGER` | `NOT NULL`, `FOREIGN KEY -> users(id)` | — | User ID of the teacher/admin who requested generation. |
| `topic` | `TEXT` | `NOT NULL` | — | Target mathematics curriculum topic slug. |
| `subconcept` | `TEXT` | `NULL` | `NULL` | Target curriculum subconcept slug. |
| `model_name` | `TEXT` | `NOT NULL` | — | Identifier of the SLM/LLM model executed. |
| `attempts` | `INTEGER` | `NOT NULL`, `CHECK(attempts >= 1)` | — | Number of generation attempts executed ($1$ to $N$). |
| `duration_ms` | `REAL` | `NOT NULL`, `CHECK(duration_ms >= 0.0)` | — | Total wall-clock execution time in milliseconds. |
| `success` | `INTEGER` | `NOT NULL`, `CHECK(success IN (0, 1))` | — | `1` if generation succeeded within max retries; `0` on unrecoverable failure. |
| `rejection_history_json` | `TEXT` | `NULL` | `NULL` | JSON-serialized list of chronological stage errors captured during intermediate rejection cycles. |
| `created_at` | `TIMESTAMP` | — | `CURRENT_TIMESTAMP` | UTC timestamp when generation request was executed. |

---

## <a id="2-match-sessions--real-time-voting"></a>2. Match Sessions & Real-Time Voting

### Table: `quiz_sessions`
Live classroom quiz sessions coordinating question presentation, real-time round progression, and vote collection.

| Column | Type | Constraints | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `TEXT` | `PRIMARY KEY` | — | Unique session identifier (UUID string). |
| `title` | `TEXT` | `NOT NULL` | — | Human-readable title of the quiz session. |
| `topic` | `TEXT` | `NOT NULL` | — | Mathematics topic slug (e.g., `'fractions'`). |
| `teacher_id` | `INTEGER` | `NULL`, `FOREIGN KEY -> users(id) ON DELETE SET NULL` | `NULL` | Host teacher account identifier. |
| `status` | `TEXT` | `NOT NULL`, `CHECK(status IN ('lobby', 'active', 'completed', 'abandoned'))` | `'lobby'` | Current state of the session lifecycle. |
| `question_count` | `INTEGER` | `NOT NULL` | `0` | Planned number of question rounds in session. |
| `current_round_index` | `INTEGER` | `NOT NULL` | `0` | 0-based index of the currently active/latest round. |
| `created_at` | `TIMESTAMP` | — | `CURRENT_TIMESTAMP` | UTC timestamp of session creation. |
| `started_at` | `TIMESTAMP` | `NULL` | `NULL` | Timestamp when session transitioned out of lobby. |
| `ended_at` | `TIMESTAMP` | `NULL` | `NULL` | Timestamp when session completed or was abandoned. |

---

### Table: `quiz_session_rounds`
Sequential question turns within a quiz match, tracking voting window timers and status.

| Column | Type | Constraints | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `TEXT` | `PRIMARY KEY` | — | Unique round identifier (UUID string). |
| `session_id` | `TEXT` | `NOT NULL`, `FOREIGN KEY -> quiz_sessions(id) ON DELETE CASCADE` | — | Reference to parent quiz session. |
| `question_id` | `TEXT` | `NULL`, `FOREIGN KEY -> quiz_questions(id) ON DELETE SET NULL` | `NULL` | Reference to diagnostic question bank entry. |
| `round_index` | `INTEGER` | `NOT NULL` | — | 0-based sequential sequence order of the round. |
| `status` | `TEXT` | `NOT NULL`, `CHECK(status IN ('pending', 'open', 'closed', 'revealed'))` | `'pending'` | Lifecycle state of this question round. |
| `opened_at` | `TIMESTAMP` | `NULL` | `NULL` | Timestamp when voting opened. |
| `closed_at` | `TIMESTAMP` | `NULL` | `NULL` | Timestamp when voting window closed. |
| `duration_seconds` | `INTEGER` | `NOT NULL` | `30` | Configured countdown timer duration in seconds. |

---

### Table: `quiz_session_votes`
Individual student vote submissions recorded immutably per round.

| Column | Type | Constraints | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `TEXT` | `PRIMARY KEY` | — | Unique vote identifier (UUID string). |
| `session_id` | `TEXT` | `NOT NULL`, `FOREIGN KEY -> quiz_sessions(id) ON DELETE CASCADE` | — | Reference to parent quiz session. |
| `round_id` | `TEXT` | `NOT NULL`, `FOREIGN KEY -> quiz_session_rounds(id) ON DELETE CASCADE` | — | Reference to active question round. |
| `student_id` | `INTEGER` | `NOT NULL`, `FOREIGN KEY -> users(id) ON DELETE CASCADE` | — | Reference to participating student. |
| `transport_type` | `TEXT` | `NOT NULL`, `CHECK(transport_type IN ('web', 'hardware', 'mock'))` | `'web'` | Ingestion transport channel. |
| `device_id` | `TEXT` | `NULL` | `NULL` | Hardware clicker ID if submitted via ESP32. |
| `selected_option` | `TEXT` | `NOT NULL`, `CHECK(selected_option IN ('A', 'B', 'C', 'D'))` | — | Option key chosen by student. |
| `is_correct` | `INTEGER` | `NOT NULL`, `CHECK(is_correct IN (0, 1))` | — | Correctness boolean flag. |
| `misconception` | `TEXT` | `NULL` | `NULL` | Diagnostic misconception tag for incorrect votes. |
| `response_time_ms` | `REAL` | `NULL`, `CHECK(response_time_ms IS NULL OR response_time_ms >= 0.0)` | `NULL` | Turnaround time from window opening to vote receipt. |
| `created_at` | `TIMESTAMP` | — | `CURRENT_TIMESTAMP` | UTC timestamp of vote submission. |

---

## <a id="3-integrity--concurrency-invariants"></a>3. Integrity & Concurrency Invariants

### <a id="a-first-press-locking-enforcement"></a>A. First-Press Locking Enforcement
To prevent a student from voting multiple times within the same question round or overwriting an earlier choice, the database layer enforces a composite unique constraint:

```sql
UNIQUE(round_id, student_id)
```

Any second attempt within the round raises an immediate `SQLITE_CONSTRAINT_UNIQUE` violation and returns HTTP `409 Conflict` to the client.

### <a id="b-question-soft-deletion--telemetry-integrity"></a>B. Question Soft-Deletion & Telemetry Integrity
When a diagnostic question is soft-deleted:
1. `deleted_at` is set to `CURRENT_TIMESTAMP`.
2. The question is excluded from default bank listings, random sampling, and session round generation.
3. Historical rounds in `quiz_session_rounds` retain their `question_id` reference, ensuring historical error telemetry and weekly diagnostic teacher reports remain 100% accurate.

---

## Related Specifications

* **[Database Hub & ER Model](README.md)**: Architecture overview, full Mermaid ER diagram, and index definitions.
* **[Quiz API Specification](../api/quiz.md)**: Question generation, schema discovery, and bank management endpoints.
* **[Quiz Sessions API Specification](../api/sessions.md)**: Match creation, round lifecycle, and voting endpoints.
* **[Diagnostic Distractors Architecture](../architecture/diagnostic-distractors.md)**: 32 misconception taxonomy.
