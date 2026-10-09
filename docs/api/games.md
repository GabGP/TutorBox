# Offline Games API (Mode 3)

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [REST API Hub](README.md) › **Games** • **Related:** [Three Modes](../architecture/three-modes.md#mode-3-offline-primary-games) • [Game Events Schema](../database/games.md) • [Week 6 Milestone](../milestones/week-6-games-sync.md)

</div>

---

The grade apps in `pwa/tareas/` will send each answer tapped to the appliance when their phone reaches
it. The appliance stores each answer once, labels it with the concepts its lesson practises, and needs
no login. The endpoint is open in every class mode. No game sends events yet: the queue that sends them
is a separate deliverable, described in [§6](#6-client-contract). Staff read the counts of what is stored
at a second endpoint ([§7](#7-summary-for-staff)). Code: `backend/src/api/games/` (HTTP),
`backend/src/modes/games/` (validation, labels, ingestion), and `game_event_repository.py` (writes) and
`game_event_summary.py` (counts) in `backend/src/core/db/`.

## Table of Contents
- [1. Endpoint](#1-endpoint)
- [2. Statuses and Errors](#2-statuses-and-errors)
- [3. Who the Events Belong To](#3-who-the-events-belong-to)
- [4. Concept Labels](#4-concept-labels)
- [5. Deduplication](#5-deduplication)
- [6. Client Contract](#6-client-contract)
- [7. Summary for Staff](#7-summary-for-staff)
- [8. Limits](#8-limits)

---

## <a id="1-endpoint"></a>1. Endpoint

| Method & path | Roles | Purpose |
| :--- | :--- | :--- |
| `POST /api/v1/games/events` | Public, Student | Stores a batch of answers tapped in a grade app. `422` only for a malformed envelope. |
| `GET /api/v1/games/events/summary` | Teacher, Admin | Counts the stored answers, in total and per lesson ([§7](#7-summary-for-staff)). |

```http
POST /api/v1/games/events
Content-Type: application/json

{
  "install_id": "3f9c1a7e5b2d4f60a8e1c9b7d2f4a6e3",
  "events": [
    {
      "client_event_id": "5b1e0c9d8a7f4e3b2c1d0e9f8a7b6c5d",
      "grade": "primero",
      "lesson_id": "sumar-jocotes",
      "round_index": 0,
      "attempt": 1,
      "is_correct": false,
      "answer": "4",
      "expected": "5",
      "misconception": "counted_one_less",
      "occurred_at": "2026-10-09T15:04:05.000Z",
      "app_version": "1.0"
    },
    {
      "client_event_id": "8d2a4f6e1c3b5a7d9e0f2c4b6a8d0e1f",
      "grade": "primero",
      "lesson_id": "sumar-jocotes",
      "round_index": 0,
      "attempt": 2,
      "is_correct": true,
      "answer": "5",
      "expected": "5",
      "occurred_at": "2026-10-09T15:04:12.000Z",
      "app_version": "1.0"
    }
  ]
}
```

```json
{
  "accepted": 2,
  "duplicates": 0,
  "rejected": 0,
  "results": ["accepted", "accepted"]
}
```

The envelope has two fields. Both are required.

| Field | Type | Rule | Meaning |
| :--- | :--- | :--- | :--- |
| `install_id` | string | 16 to 64 characters from `A-Z`, `a-z`, `0-9`, `_` and `-`. | A random id that the app generates once and keeps. It tells one phone or browser from another. |
| `events` | array | 1 to 200 items. | The answers to store. Each item is checked on its own. |

Each item in `events` is one answer tapped. Right answers are sent too, so that error rates have a
denominator. An event has these fields:

| Field | Type | Rule | Meaning |
| :--- | :--- | :--- | :--- |
| `client_event_id` | string | Required. 16 to 64 characters from `A-Z`, `a-z`, `0-9`, `_` and `-`. | An id generated on the phone for this answer. It is stored once. |
| `grade` | string | Required. 3 to 16 lowercase letters. | The grade app, for example `primero`, `segundo` or `tercero`. An unknown grade is accepted. |
| `lesson_id` | string | Required. 1 to 64 characters from `a-z`, `0-9` and `-`. | The lesson id in the app's registry (`pwa/tareas/<grade>/public/js/data/modules.js`). An unknown lesson is accepted. |
| `round_index` | integer | Required. 0 to 999. | The round of the lesson. |
| `attempt` | integer | Required. 1 to 99. | The tap number within the round. `1` is the first tap of the round. |
| `is_correct` | boolean | Required. JSON `true` or `false` only. | Whether the tapped answer was right. Numbers and text make the event `rejected`. |
| `occurred_at` | string | Required. A date and time with a timezone, for example `2026-10-09T15:04:05.000Z`. | When the answer was tapped, by the phone's clock. Stored in UTC, to the second. |
| `answer` | string | Optional. At most 64 characters. | The answer tapped. |
| `expected` | string | Optional. At most 64 characters. | The right answer for the round. |
| `app_version` | string | Optional. At most 16 characters. | The version of the app that sent the event. |
| `misconception` | string | Optional. A snake_case slug of 2 to 64 characters: a lowercase letter, then lowercase letters, digits and `_`. | The mistake that the tapped wrong choice stands for ([§4](#4-concept-labels)). It is stored only when `is_correct` is `false`. |

Unknown fields are ignored, in the envelope and in each event. A newer app can therefore report to an
older appliance.

---

## <a id="2-statuses-and-errors"></a>2. Statuses and Errors

A well-formed envelope always gets `200 OK`, even when every event in it is rejected. The events of a
batch are written in one commit. The body counts the events and gives one status per event, in the order
sent. For a batch of three events in which the second one was already stored:

```json
{
  "accepted": 2,
  "duplicates": 1,
  "rejected": 0,
  "results": ["accepted", "duplicate", "accepted"]
}
```

| Status | Meaning | Stored |
| :--- | :--- | :--- |
| `accepted` | The event is stored now. | Yes |
| `duplicate` | An event with that `client_event_id` was already stored. The first delivery wins: the repeated one changes nothing. | The first copy stays |
| `rejected` | The event is malformed. It is rejected alone: the other events of the batch are still stored. | No |

| HTTP | When | Stored |
| :--- | :--- | :--- |
| `200 OK` | The envelope is well formed. Each event then has its own status. | Per event |
| `422 Unprocessable Content` | The body is not JSON or not an object. `install_id` is missing or invalid. `events` is missing, empty, not a list, or has more than 200 items. | Nothing |

The `422` body is FastAPI's validation error. Its `detail` is a list that names each failing field.

---

## <a id="3-who-the-events-belong-to"></a>3. Who the Events Belong To

The endpoint reads the login token if one is sent. A bad token never refuses the events.

| Request | `student_id` of each stored event |
| :--- | :--- |
| `Authorization: Bearer <token>` of a valid student login | The id of that student |
| No `Authorization` header | `NULL` |
| An invalid, malformed or expired token, or a logged-out token | `NULL` |
| A teacher or admin login | `NULL` |

With a well-formed envelope, every row of this table still gets `200 OK`. An expired login must not block a phone's queue. A student
who still has to change the PIN has a valid login, so that student's events keep the student id. The
check is `optional_student_id` in `backend/src/api/games/identity.py`.

---

## <a id="4-concept-labels"></a>4. Concept Labels

When an event is stored, its lesson is looked up in
[`lesson_topics.json`](../../backend/src/modes/games/lesson_topics.json). The table maps each grade and
lesson id to a CNB topic id. It covers the 77 lessons of the three apps: 21 in `primero`, 26 in `segundo`
and 30 in `tercero`. The labels use the same vocabularies as the tutor's `turn_logs` (see
[dialogue.md §2.1](../database/dialogue.md#21-telemetry-label-vocabularies)).

* **`cnb_topic`**: a topic id from [`cnb_matematicas.json`](../../backend/src/modes/socratic/cnb_matematicas.json).
  It is set for every known lesson.
* **`concept_topic` and `concept_subconcept`**: a pair from the quiz taxonomy (`CURRICULUM_TAXONOMY` in
  [`taxonomy.py`](../../backend/src/modes/quiz/contracts/taxonomy.py)). It is set only for the four CNB
  topics below. Every other lesson has `NULL` in both.

The lesson id is looked up within its own grade. `fracciones` exists in `segundo` and in `tercero`, so the
key is the pair of grade and lesson id.

| CNB topic | `concept_topic` | `concept_subconcept` | Lessons (`grade/lesson_id`) |
| :--- | :--- | :--- | :--- |
| `suma_resta` | `arithmetic` | `addition_subtraction` | `primero/sumar-jocotes`, `primero/restar-elotes`, `segundo/sumar-restar`, `tercero/sumas-restas` |
| `multiplicacion` | `arithmetic` | `multiplication_division` | `segundo/multiplicar`, `tercero/multiplicar-repartir` |
| `division` | `arithmetic` | `multiplication_division` | `tercero/division-residuo` |
| `fracciones` | `fractions` | `NULL` | `segundo/fracciones`, `tercero/fracciones` |

* An unknown grade or lesson is stored with all three labels set to `NULL`. Its `grade` and `lesson_id`
  are stored too, so such rows can be labelled later.

**`misconception`** is the one label that comes from the phone. The appliance cannot work it out: an
event carries the value tapped and the right value, and not the numbers of the exercise. The lesson
author knows which mistake each wrong choice stands for, so the game names it.

* The slug is stored as sent, in `game_events.misconception`. It is the counterpart of the misconception
  of a quiz distractor and of `turn_logs.error_type` in the tutor.
* When a quiz taxonomy slug fits the lesson's pair, send that slug, for example `borrowing_error` or
  `added_instead_of_subtracted` in an `addition_subtraction` lesson. The weekly report can then count the
  same mistake across the quiz, the tutor and the games. Otherwise send a new slug: the column has no
  fixed vocabulary.
* A right answer never stores a misconception, whatever the game sent.
* A value that is not a slug makes its event `rejected`.
* No lesson tags its wrong choices yet, so every event stored today has `NULL` here.

The tests in `backend/tests/modes/games/test_labels.py` keep the table honest:

* The table holds exactly the lessons that each registry in `pwa/tareas/` ships.
* Every CNB topic exists in `cnb_matematicas.json` and is taught in the grade of its lesson.
* Every taxonomy pair is valid in the quiz taxonomy.
* A CNB topic gets the same taxonomy pair that the tutor gives it.

---

## <a id="5-deduplication"></a>5. Deduplication

`game_events.client_event_id` is `UNIQUE`. The insert ends with `ON CONFLICT(client_event_id) DO NOTHING`,
so a repeated event stores nothing and does not fail its batch. A phone that resends its queue after a
lost reply is therefore safe.

The concurrency tests in `backend/tests/api/games/test_games_concurrency.py` prove this under parallel
load:

* Eight simultaneous posts of the same 25 events store 25 rows. Across the eight replies there are 25
  `accepted` events and 175 `duplicate` events.
* Ten phones, each posting its own 20 events at the same time, store all 200 events.

---

## <a id="6-client-contract"></a>6. Client Contract

This section is for the person who adds the queue to the games in `pwa/tareas/`. No game does this yet.
The steps below are the client side of the contract. The event shape is the one in
[§1](#1-endpoint).

1. On every answer tapped, right or wrong, append one event to a queue kept in `localStorage`.
2. Build `client_event_id` and `install_id` from `crypto.getRandomValues()`, for example 16 random bytes
   written as 32 hex characters. Generate `install_id` once and keep it. `crypto.randomUUID()` is not
   available there: the appliance serves plain `http://tutorbox`, which is not a secure context.

   ```js
   function randomHexId() {
     const bytes = crypto.getRandomValues(new Uint8Array(16));
     return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
   }
   ```

3. `attempt` starts at 1 for each round and grows with every tap in that round. `occurred_at` is
   `new Date().toISOString()`.
4. Send the queue when a lesson ends, when the app opens and on the browser's `online` event. Send at most
   200 events per request. The page and the API share the origin, so no CORS setup is needed.
5. If `localStorage` holds the login token of `/alumno/` (key `tb_token`), send it as
   `Authorization: Bearer <token>`. Otherwise send no `Authorization` header.
6. On HTTP 200, remove every event of that batch from the queue, whatever its status. All three statuses
   are final: a rejected event would be rejected again.
7. On a network error, or any other status, keep the queue and try again later. Sending the same events
   again is safe.
8. "Later" means the next trigger of step 4. Never retry in a loop or on a short timer. nginx answers
   `429` to an address that posts more than 30 times a minute after a burst of 20
   ([§8](#8-limits)), and a queue that retries at once would stay locked out.
9. Cap the queue: drop the oldest events past a fixed size. A phone that never reaches the appliance must
   not fill its storage.
10. Never put the child's name or the parent PIN of the game profile in an event.
11. Optional: give each wrong choice of a lesson a `misconception` slug and send it with the event
    ([§4](#4-concept-labels)).

---

## <a id="7-summary-for-staff"></a>7. Summary for Staff

`GET /api/v1/games/events/summary` counts the stored answers. It needs a teacher or admin login (`401`
without one, `403` for a student).

| Query parameter | Rule | Meaning |
| :--- | :--- | :--- |
| `install_id` | Optional. Same rule as the `install_id` of a batch; `422` otherwise. | Counts the events of that phone or browser only. |

```json
{
  "events": 4,
  "wrong_events": 3,
  "installs": 2,
  "lessons": [
    {
      "grade": "primero",
      "lesson_id": "sumar-jocotes",
      "cnb_topic": "suma_resta",
      "concept_topic": "arithmetic",
      "concept_subconcept": "addition_subtraction",
      "events": 3,
      "wrong_events": 2
    }
  ]
}
```

* `events` is the number of stored answers, `wrong_events` the number with `is_correct` false, and
  `installs` the number of different `install_id` values.
* `lessons` has one item per grade and lesson id, with the most wrong answers first. It holds at most 200
  items, because a lesson id is whatever a phone sent.
* **Use in the sync test**: play with the phone away from the appliance, count the taps, reconnect, and
  read the summary with that phone's `install_id`. `events` must equal the number of taps. Every id is
  stored once, so a lower number means lost events and a higher one cannot happen.

---

## <a id="8-limits"></a>8. Limits

* **Rate limit in nginx only.** [`tutorbox.conf`](../../infra/nginx/tutorbox.conf) allows each address 30
  posts a minute to `POST /api/v1/games/events` after a burst of 20, and answers `429` beyond that. A
  phone posts once or twice per lesson. The reason is the database: every batch takes SQLite's one
  write lock, which quiz votes also need, so a game stuck in a retry loop must not reach the backend.
  The backend itself has no limit, and uvicorn also listens on port 8000, where nginx is not in front.
* **Events can be invented.** The endpoint needs no login, so anyone on the classroom network can post
  valid events, slowly enough to pass the limit. Events with a `student_id` come from a logged-in
  student; the others are anonymous.
* **Request size.** The backend sets no request size limit. `tutorbox.conf` does not set
  `client_max_body_size`, so nginx's default of 1 MB applies in front of the endpoint.
* **Clocks.** `occurred_at` comes from the phone's clock, so a phone with a wrong clock stores wrong
  times. `received_at` is the appliance's clock. See [Game Events Schema](../database/games.md#2-invariants).
* **No client yet.** No game sends events. The queue is described in [§6](#6-client-contract).
