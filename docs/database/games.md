# Mode 3: Offline Games Event Schema

Technical specification for the answer events that the grade apps in `pwa/tareas/` send to the appliance,
one row per answer tapped.

<div align="center">

| 🏠 [Utz'tutor](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Database](README.md) › **Game Events** • **Related:** [Core Schema](core.md) • [Dialogue Telemetry](dialogue.md) • [Games API](../api/games.md)

</div>

---

## Table of Contents
- [1. Data Dictionary: `game_events`](#1-data-dictionary-game_events)
- [2. Invariants](#2-invariants)
- [Related Specifications](#related-specifications)

---

## <a id="1-data-dictionary-game_events"></a>1. Data Dictionary: `game_events`

Stores one row per answer tapped in a grade app. Migration
[`013_add_game_events.sql`](../../backend/migrations/013_add_game_events.sql) creates the table and
[`014_add_game_event_misconception.sql`](../../backend/migrations/014_add_game_event_misconception.sql)
adds `misconception`. The repository
[`game_event_repository.py`](../../backend/src/core/db/game_event_repository.py) writes the rows, and
[`game_event_summary.py`](../../backend/src/core/db/game_event_summary.py) counts them for the staff
summary ([Games API §7](../api/games.md#7-summary-for-staff)).

| Column | Type | Constraints | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | — | Unique row ID. |
| `client_event_id` | `TEXT` | `NOT NULL`, `UNIQUE` | — | Answer id generated on the phone. Its `UNIQUE` constraint makes a repeated delivery harmless. |
| `install_id` | `TEXT` | `NOT NULL` | — | Random id that the app generates once and keeps. It tells one phone or browser from another. |
| `student_id` | `INTEGER` | `NULL`, `REFERENCES users(id) ON DELETE SET NULL` | `NULL` | The logged-in student who sent the event. `NULL` when no student login was sent. |
| `grade` | `TEXT` | `NOT NULL` | — | The grade app, for example `primero`, `segundo` or `tercero`. Any value the API accepts is stored. |
| `lesson_id` | `TEXT` | `NOT NULL` | — | The lesson id in the app's registry. Any value the API accepts is stored. |
| `round_index` | `INTEGER` | `NOT NULL`, `CHECK(round_index >= 0)` | — | The round of the lesson. The API accepts 0 to 999. |
| `attempt` | `INTEGER` | `NOT NULL`, `CHECK(attempt >= 1)` | — | The tap number within the round. `1` is the first tap. The API accepts 1 to 99. |
| `is_correct` | `INTEGER` | `NOT NULL`, `CHECK(is_correct IN (0, 1))` | — | `1` if the tapped answer was right, `0` otherwise. |
| `answer` | `TEXT` | `NULL` | `NULL` | The answer tapped. At most 64 characters. |
| `expected` | `TEXT` | `NULL` | `NULL` | The right answer for the round. At most 64 characters. |
| `app_version` | `TEXT` | `NULL` | `NULL` | Version of the app that sent the event. At most 16 characters. |
| `occurred_at` | `TEXT` | `NOT NULL` | — | Time of the tap in UTC, `YYYY-MM-DD HH:MM:SS`, from the phone's clock. See [§2](#2-invariants). |
| `received_at` | `TIMESTAMP` | `NULL` | `CURRENT_TIMESTAMP` | Time the appliance stored the row, from the appliance's clock. |
| `cnb_topic` | `TEXT` | `NULL` | `NULL` | CNB topic id from `cnb_matematicas.json`, set from the lesson. See [§2](#2-invariants). |
| `concept_topic` | `TEXT` | `NULL` | `NULL` | Quiz taxonomy topic (`CURRICULUM_TAXONOMY` key), set for four CNB topics. See [§2](#2-invariants). |
| `concept_subconcept` | `TEXT` | `NULL` | `NULL` | Quiz taxonomy subconcept paired with `concept_topic`. It is `NULL` when `concept_topic` is `fractions`. See [§2](#2-invariants). |
| `misconception` | `TEXT` | `NULL` | `NULL` | The mistake behind a wrong answer, as a snake_case slug that the game sends. `NULL` on a right answer and when the game sent none. See [§2](#2-invariants). |

---

## <a id="2-invariants"></a>2. Invariants

* **One row per client event id**: `client_event_id` is `UNIQUE`, and the insert ends with
  `ON CONFLICT(client_event_id) DO NOTHING`. A repeated id stores nothing, and the first stored row stays
  unchanged. The API reports that repeat as `duplicate` ([Games API §5](../api/games.md#5-deduplication)).
* **Labels are set at ingestion**: `cnb_topic`, `concept_topic` and `concept_subconcept` are filled when
  the row is stored, from the lesson table in `backend/src/modes/games/lesson_topics.json`. An unknown grade
  or lesson leaves all three `NULL`. The row keeps `grade` and `lesson_id`, so it can be labelled later.
* **Open vocabularies**: as in migration 012, the label columns have no `CHECK` constraint. The
  vocabularies live in code and tests, so they can grow without a migration.
* **The misconception comes from the phone**: it is the one label that the appliance does not set. The API
  accepts any snake_case slug of 2 to 64 characters and stores it only on a wrong answer
  ([Games API §4](../api/games.md#4-concept-labels)). It plays the part of `turn_logs.error_type` in the
  tutor. No lesson sends one yet, so the column is `NULL` in every row stored today.
* **Two clocks**: `occurred_at` is the phone's clock. It holds the time of the tap converted to UTC, stored
  to the second, so fractions of a second are dropped. It is wrong when the phone's clock is wrong.
  `received_at` is the appliance's clock: the database sets it to `CURRENT_TIMESTAMP` (UTC) when the row is
  inserted.
* **Student link**: `student_id` is set only for a valid student login. Deleting a `users` row sets
  `student_id` to `NULL` and keeps the event. A soft-deleted account keeps its id, because its `users` row
  stays in the table.
* **Lifecycle**: the application only inserts rows. No code path updates or deletes a `game_events` row.
* **Index**: `idx_game_events_concept` on `(concept_topic, concept_subconcept)` serves the aggregation of
  answers per concept.

---

## Related Specifications

* **[Database Hub & ER Model](README.md)**: Architecture overview and full Mermaid ER diagram.
* **[Games API](../api/games.md)**: The endpoint that writes these rows, and the client contract.
* **[Dialogue Telemetry](dialogue.md)**: The label vocabularies that `cnb_topic` and the taxonomy pair share with `turn_logs`.
* **[Week 6 Milestone](../milestones/week-6-games-sync.md)**: Status of the games and sync work.
