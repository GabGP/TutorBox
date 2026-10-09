# Week 6 Milestone: Offline Primary Games & Log Synchronization

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Milestones](roadmap.md) › **Week 6 Milestone** • **Related:** [Engineering Roadmap](roadmap.md) • [Three Modes](../architecture/three-modes.md) • [Games API](../api/games.md) • [Game Events Schema](../database/games.md) • [Take-Home Apps](../../pwa/README.md#3-tareas--take-home-math-apps-tareas) • [Android Wrapper](../../pwa/tareas/android/README.md)

</div>

---

This document tracks the technical deliverables, architectural implementations, and quality metrics of the **Week 6 Milestone** by **Student A (Pilot: Game Error Ingestion & Idempotent Deduplication)** and **Student B (Copilot: Offline Game Hosting & Client-Side Sync Queue)**. It records the state of the repository on 2026-10-08.

---

## 1. Executive Summary & Verification Metrics

* **Theme**: *"Opportunistic Synchronization: Data that survives disconnection"*
* **Status**: **Pilot (Student A) Complete & Green · Copilot (Student B) Hosting in Place, Sync Queue Not Started**
* **Backend Test Suite**: **2006 / 2006 passing tests** (213 new this week: `tests/modes/games/`, `tests/api/games/` and the two `game_event` files in `tests/core/db/`).
* **Statement Coverage**: **100.00% statement coverage** across all 6,518 source statements (`pyproject.toml` enforces `--cov-fail-under=100`).
* **Linter & Formatter**: **0 errors, 0 warnings** (`pre-commit run --all-files` clean across all 7 hooks).
* **Modularity Compliance**: **100% of production source files $\le 150$ LoC** and **100% of test files $\le 300$ LoC**, validated by `tests/test_modularity_policy.py` (largest games module: `modes/games/ingest.py`, 74 lines).
* **Game Content Checks**: **77 lessons and 336 choice rounds** pass `tests/check-lessons.mjs` (Primero 21 lessons / 48 rounds, Segundo 26 / 129, Tercero 30 / 159): every lesson loads its own file and every round has exactly one right answer.
* **Acceptance Criteria Status**:
  * ⏳ **Games playable completely offline from the appliance on 3 client devices**: the three grade apps are served by the appliance and request nothing from outside it. No observation on three devices is recorded yet.
  * ⏳ **Disconnection sync test (play offline, reconnect, 100% of error events ingested, 0 duplicates)**: the appliance half is proven in CI. Eight phones resending the same 25 events store 25 rows, and ten phones with 20 events each store all 200 (`test_games_concurrency.py`). The test on real devices waits for the client queue, which no game has yet.
* **Key Milestone Artifacts**:
  * **Ingestion Endpoint**: `POST /api/v1/games/events` stores each answer tapped once per client event id and answers with one status per event ([Games API](../api/games.md)).
  * **Lesson Concept Table**: all 77 lessons of the three grade apps mapped to the CNB topic the tutor already uses, and to the quiz taxonomy pair where the quiz has that concept.
  * **Event Storage**: migration `013` creates `game_events` with `UNIQUE(client_event_id)` ([Game Events Schema](../database/games.md)).
  * **Three Grade Apps, Appliance Hosting, Android Wrapper and Class Mode `apps`**: in the repository before Week 6 began (Section 2.B).

---

## 2. Implemented Subsystems by Lead

### A. Student A (Pilot Scope: Game Error Ingestion & Idempotent Deduplication)

**Design Decision (Pilot, 2026-10-08): ingestion plus classroom browser sync.** The appliance receives events from the copy of the games it serves at `http://tutorbox/tareas/<grade>/`. Sync from the take-home APK is left out: the APK has no `INTERNET` permission, on purpose, and changing that means new signed APKs on every family phone. The endpoint does not depend on that choice, so an APK bridge can be added later without changing it.

**Delivered Subsystems:**

1. **Event Contract (`backend/src/modes/games/events.py`)**:
   * One event is one answer tapped, right or wrong: an id generated on the phone, grade, lesson id, round, attempt number, the value tapped, the right value and the phone's time. Right taps are part of the contract because an error count needs the number of attempts beside it.
   * Unknown fields are ignored and an unknown grade or lesson is valid, so a game newer than the appliance still reports.
   * A timestamp must carry a timezone and is converted to UTC. One that leaves the calendar when converted is a validation error, not a crash.
2. **Storage & Idempotent Deduplication (`backend/migrations/013_add_game_events.sql`, `backend/src/core/db/game_event_repository.py`)**:
   * `game_events.client_event_id` is `UNIQUE`, and the insert uses `ON CONFLICT(client_event_id) DO NOTHING` and reports whether a row was written. The first delivery wins.
   * The conflict clause names that one column: any other broken constraint still raises.
   * Deleting a user sets `student_id` to `NULL` and keeps the event.
3. **Concept Normalizer (`backend/src/modes/games/labels.py`, `lesson_topics.json`)**:
   * A table from (grade, lesson id) to a CNB topic id for the 77 lessons. The pair is the key because the same lesson id exists in two grades with other content (`fracciones`).
   * Four CNB topics also have a quiz `CURRICULUM_TAXONOMY` pair: `suma_resta`, `multiplicacion`, `division` and `fracciones`. The other lessons (ubicación, patrones, conjuntos, geometría, medidas, tiempo and the rest) keep their CNB topic alone, as a tutor concept question does.
   * The table lives on the appliance because an APK or a cached page changes only when a family installs or reloads it. The phone sends what happened; the appliance decides what it is called.
   * `test_labels.py` fails when a lesson ships without an entry: it reads the three `modules.js` registries and compares them with the table. It also checks every topic against `cnb_matematicas.json` and its grades, every pair against the quiz taxonomy, and every CNB topic against the pair the tutor gives it.
4. **Ingestion Service (`backend/src/modes/games/ingest.py`)**:
   * Each event of a batch is validated on its own and gets one status: `accepted`, `duplicate` or `rejected`.
   * A malformed event is rejected alone. If it failed the whole batch, the phone would send the same batch forever and its queue would never empty.
5. **Endpoint & Optional Identity (`backend/src/api/games/`)**:
   * `POST /api/v1/games/events` takes `{install_id, events}` with 1 to 200 events, in every class mode, and stores the batch in one transaction.
   * No login is needed. A valid student token ties the rows to that student. A missing, invalid, expired or logged-out token, or a staff login, stores them without a student instead of refusing them: an expired login must not block a queue.
6. **Verification (`backend/tests/`)**:
   * `test_games_api.py` (20 tests): new events, the same batch twice, overlapping batches, a malformed event among valid ones, the six envelope errors and every identity case.
   * `test_games_concurrency.py` (2 tests): the two load cases of the acceptance criterion.
   * `test_events.py` (32 tests), `test_ingest.py` (16), `test_labels.py` (124), `test_game_event_repository.py` (10) and `test_game_event_migration_013.py` (9).

**Interface Contract Provided by Student A for Student B's Queue:** [Games API §6](../api/games.md), the steps a game follows to record, send and forget events.

**Not Built, by Decision:**

* **Misconception Labels**: Segundo and Tercero build their choices with `pickChoices(answer, [wrong, wrong])`, and 20 lesson files name in their header the mistake a wrong answer stands for (in `tercero/.../division-residuo.js`, `80 ÷ 2` offers `4` and `160`). No choice carries a slug, so an event stores the value tapped and no misconception.
* **Rate Limit**: the endpoint has none and needs no login. On the classroom network anyone can post valid events.
* **Read Endpoint**: nothing lists or counts stored events yet. The Week 8 report reads the table.

**What Still Stands Between the Games and Live Data:**

1. **The APK sends nothing, on purpose**: it has no `INTERNET` permission ([Android Wrapper](../../pwa/tareas/android/README.md): *"Nothing leaves the phone"*). Its page runs on `https://appassets.androidplatform.net/`, so a request to `http://tutorbox` is cleartext, cross-origin and mixed content. Sync from the APK needs the permission, a cleartext exception for the appliance, a native bridge in the style of `AndroidTTS`, and new signed APKs.
2. **The browser copy can send but cannot play offline**: `http://tutorbox/tareas/<grade>/` shares its origin with the API, so it can post with no CORS. Plain HTTP has no service worker, so the page does not open away from the appliance; "play offline, then reconnect" is limited there to a Wi-Fi drop while the page is open. `crypto.randomUUID()` is also absent on plain HTTP, so event ids must be built from `crypto.getRandomValues()`.
3. **A game has no TutorBox student**: the child's profile is a name, an avatar and an optional parent PIN in `localStorage`, and mode `apps` asks for no login. An event is tied to a `users` row only when the game sends the login token that `/alumno/` keeps under the same origin (`tb_token`). The parent PIN is stored as typed and must never travel with an event.
4. **Only Primero has an APK in the repository**: `pwa/tareas/descargas/` holds `primero.apk`; the download page hides a grade whose APK is missing.

---

### B. Student B (Copilot Scope: Offline Game Hosting & Client-Side Sync Queue)

**Baseline Already in Place (in the repository between 2026-09-23 and 2026-09-29):**

1. **Three Grade Apps (`pwa/tareas/primero/`, `segundo/`, `tercero/`)**:
   * One app per grade, seven modules each, one module per CNB mathematics competencia of that grade; every lesson is registered with a CNB content number of its module (`public/js/data/modules.js`).
   * "Look, listen, tap the answer": a wrong tap never ends a round, the child hears a hint and tries again. 68 of the 77 lessons extend `ChoiceLesson` (`lessons/shared/choice-lesson.js`), where every tap passes through `_answer`; the 9 oldest Primero lessons carry their own feedback code.
   * Fonts, drawings and sounds are bundled and every path is relative, so the same `public/` folder runs on the appliance and inside the APK. No file in the three `public/` folders names an external address.
2. **Appliance Hosting (`backend/src/main.py`, `backend/src/api/captive.py`)**:
   * `REPO_MOUNTS` serves `/tareas/primero/`, `/tareas/segundo/`, `/tareas/tercero/` and `/descargas/` straight from the repository; the captive portal treats both prefixes as reserved.
   * `tests/api/test_repo_mounts.py` (8 tests): each grade app answers with its relative assets, the download page lists the three grades, and an APK is served as an Android package.
3. **Offline Android Wrapper (`pwa/tareas/android/`)**:
   * One `Activity` with a `WebView` and one product flavor per grade; the lessons are packed from `../<grade>/public` at build time, and the phone's text-to-speech is exposed as `window.AndroidTTS`.
   * No service worker and no `INTERNET` permission.
4. **Family Download Page (`pwa/tareas/descargas/`)**: grade menu, install steps in Spanish and the APK links.
5. **Class Mode `apps` (`pwa/app/src/features/mode/`, [`GET`/`PUT /api/v1/mode`](../api/system.md#classroom-mode))**: the teacher picks "llevar a casa"; student phones show the grade menu (download the app or play it in the browser) with no login, and the classroom screen shows `tutorbox/descargas`.

**Not Started:**

* **Client-Side Event Queue**: no game writes an event to `localStorage` or IndexedDB. A lesson keeps only how many rounds were right on the first try, and `saveLesson` stores the best star count per lesson (`kuk_progress_v1`, `kuk2_progress_v1`, `kuk3_progress_v1`).
* **Background Sync on AP Reconnection**: the only `fetch` in the three apps is the service worker's cache fill, which does not run on the appliance or in the APK.

---

## 3. Tuesday Jury Defense Package (Copilot B Defense Script)

* **Topic**: *"Opportunistic Synchronization: Data that survives disconnection"*
* **Presenter**: Student B (Copilot)

### Key Talking Points for the Jury:

1. **Offline-First Game Hosting and Caching Architecture**:
   * One `public/` folder per grade, served by the appliance and packed into the APK, with nothing loaded from outside.
   * Why an APK and not an installable PWA: browsers run service workers only over HTTPS, and the appliance serves plain `http://tutorbox`.
2. **Client-Side Event Queuing and Deduplicated Background Synchronization**:
   * The phone delivers at least once: it resends whatever it could not confirm. The appliance stores each id once. Together an event is stored exactly once.
   * Shown in CI today: the same 25 events posted by eight clients at the same time leave 25 rows, with 25 accepted and 175 duplicates across the eight replies.
   * Not shown yet: a phone doing it. The queue in the games is not built.
3. **Conceptual Error Alignment Across Quiz, Tutor and Games Modes**:
   * The three modes now share one vocabulary: the quiz taxonomy pair in `quiz_questions`, `turn_logs` and `game_events`, and the CNB topic in `turn_logs` and `game_events`.
   * A first-grade lesson on position has no quiz concept. It still has a CNB topic, so it can be counted beside a tutor question on the same topic.
   * The games stop at the concept: the quiz stores the misconception of the distractor chosen, the tutor infers one from the value typed, and a game event has none yet.
