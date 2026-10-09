# Week 6 Milestone: Offline Primary Games & Log Synchronization

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Milestones](roadmap.md) › **Week 6 Milestone** • **Related:** [Engineering Roadmap](roadmap.md) • [Three Modes](../architecture/three-modes.md) • [Take-Home Apps](../../pwa/README.md#3-tareas--take-home-math-apps-tareas) • [Android Wrapper](../../pwa/tareas/android/README.md) • [Dialogue Telemetry](../database/dialogue.md)

</div>

---

This document tracks the technical deliverables, architectural implementations, and quality metrics of the **Week 6 Milestone** by **Student A (Pilot: Game Error Ingestion & Idempotent Deduplication)** and **Student B (Copilot: Offline Game Hosting & Client-Side Sync Queue)**. It records the state of the repository on 2026-10-08, before any Week 6 code was written.

---

## 1. Executive Summary & Verification Metrics

* **Theme**: *"Opportunistic Synchronization: Data that survives disconnection"*
* **Status**: **Pilot (Student A) Not Started · Copilot (Student B) Hosting in Place, Sync Queue Not Started**
* **Backend Test Suite**: **1793 / 1793 passing tests**, unchanged since Week 5: no backend code was written this week. 8 of them cover the game mounts (`tests/api/test_repo_mounts.py`).
* **Statement Coverage**: **100.00% statement coverage** (`pyproject.toml` enforces `--cov-fail-under=100`).
* **Game Content Checks**: **77 lessons and 336 choice rounds** pass `tests/check-lessons.mjs` (Primero 21 lessons / 48 rounds, Segundo 26 / 129, Tercero 30 / 159): every lesson loads its own file and every round has exactly one right answer.
* **Acceptance Criteria Status**:
  * ⏳ **Games playable completely offline from the appliance on 3 client devices**: the three grade apps are served by the appliance and request nothing from outside it. No observation on three devices is recorded yet.
  * ⏳ **Disconnection sync test (play offline, reconnect, 100% of error events ingested, 0 duplicates)**: not started. No game stores or sends an error event, and the appliance has no endpoint to receive one.
* **Key Milestone Artifacts** (all in the repository before Week 6 began):
  * **Three Grade Apps**: `pwa/tareas/primero/`, `segundo/` and `tercero/`, CNB mathematics with Q'uq' the quetzal, vanilla ES modules and Canvas, no build step.
  * **Appliance Hosting**: `/tareas/<grade>/` and `/descargas/`, mounted from the repository by `REPO_MOUNTS` in `backend/src/main.py`.
  * **Offline Android Wrapper**: `pwa/tareas/android/`, one APK per grade with every lesson inside it.
  * **Class Mode `apps`**: the teacher's mode picker sends every student phone to the grade menu.

---

## 2. Implemented Subsystems by Lead

### A. Student A (Pilot Scope: Game Error Ingestion & Idempotent Deduplication)

**Not started.** `backend/src/modes/games/` holds a docstring only. There is no migration after `012`, no `/api/v1/games` router and no table for game events.

**How the Planned Scope Fits the Games as Built** (design notes for the Pilot, not decisions):

1. **What a game error event is**:
   * A wrong tap. 68 of the 77 lessons extend `ChoiceLesson` (`lessons/shared/choice-lesson.js`), where every wrong tap passes through one branch of `_answer`. The 9 oldest Primero lessons carry their own feedback code.
   * At that moment the app knows the grade, the module, the lesson id and its CNB content number (`screens/lesson.js`), the round, the value tapped and the right value.
   * Today all of it is discarded. A lesson keeps only how many rounds were right on the first try, turns that into 1 to 3 stars, and `saveLesson` stores the best star count per lesson.
2. **The wrong answers are designed, as in the quiz**:
   * Segundo and Tercero build their choices with `pickChoices(answer, [wrong, wrong])`, and 20 lesson files name in their header the mistake a wrong answer stands for. Example (`tercero/.../division-residuo.js`): `80 ÷ 2` offers `4` (place value) and `160` (multiplied instead of divided).
   * This is the quiz's diagnostic distractor without a misconception slug attached to the choice.
3. **What "normalizing to the concept taxonomy" means here**:
   * The games name content by grade, lesson id and CNB content number. Module numbers do not carry across grades: `m1` is Ubicación in Primero and Patrones in Segundo.
   * The shared vocabulary already exists. Since migration `012` a tutor turn is labeled with a `cnb_topic` (24 ids in `modes/socratic/cnb_matematicas.json`, 1.º–5.º primaria, among them `ubicacion`, `patrones`, `conjuntos`, `geometria`, `medidas`, `tiempo` and `problemas`) and with the quiz's `CURRICULUM_TAXONOMY` pair where the quiz has that concept.
   * A game normalizer is therefore a table from (grade, lesson id) to those same labels: a `cnb_topic` for all 77 lessons, a taxonomy pair for the arithmetic and fraction lessons, and a misconception only where a lesson tags its wrong choice.
   * The table belongs on the appliance because an APK on a family's phone changes only when the family installs a new one. The phone sends what happened; the appliance decides what it is called.
4. **Why deduplication is needed**:
   * A phone that posts a batch and leaves the AP before the response arrives cannot know whether the batch was stored, so it must send it again.
   * An id generated on the phone for each event, a `UNIQUE` constraint and an insert that ignores conflicts make the second delivery harmless. This is the pattern of the first-press lock (`UNIQUE(round_id, student_id)`).
5. **Errors need a denominator**:
   * Ten wrong taps mean one thing after 12 rounds and another after 200. The quiz has total votes and the tutor has turns; game events need the rounds played as well as the wrong taps.

**What Stands Between the Games and Live Data:**

1. **The APK sends nothing, on purpose**: it has no `INTERNET` permission ([Android Wrapper](../../pwa/tareas/android/README.md): *"Nothing leaves the phone"*). Its page runs on `https://appassets.androidplatform.net/`, so a request to `http://tutorbox` is cleartext, cross-origin and mixed content. Sync from the APK needs the permission, a cleartext exception for the appliance, a native bridge in the style of `AndroidTTS`, and new signed APKs installed on every family phone.
2. **The browser copy can send but cannot play offline**: `http://tutorbox/tareas/<grade>/` shares its origin with the API, so it can post with no CORS. Plain HTTP has no service worker, so the page does not open away from the appliance; "play offline, then reconnect" is limited there to a Wi-Fi drop while the page is open. `crypto.randomUUID()` is also absent on plain HTTP, so event ids must be built from `crypto.getRandomValues()`.
3. **A game has no TutorBox student**: the child's profile is a name, an avatar and an optional parent PIN in `localStorage`, and mode `apps` asks for no login. An event can be tied to a `users` row only if the game reads the login token that `/alumno/` keeps under the same origin (`tb_token`), which exists only when the child logged in with that same browser. The parent PIN is stored as typed and must never travel with an event.
4. **Only Primero has an APK in the repository**: `pwa/tareas/descargas/` holds `primero.apk`; the download page hides a grade whose APK is missing.

**Open Decision (Pilot):**

| Option | What is built | What it costs |
| :--- | :--- | :--- |
| **1. Close Mode 3 as take-home apps** | Nothing. The roadmap's Week 6 scope is amended, as the Week 5 install criterion was. | The Week 8 report covers two modes, the Week 9 load has no game ingestion, and the Pilot has no deliverable. |
| **2. Ingestion plus classroom browser sync** | Student A: endpoint, normalizer and deduplication. Student B: an event queue in the lesson engine that posts to the same origin. | Take-home play, the use the mode is named for, stays invisible to the teacher. The sync test is shown by switching Wi-Fi off and on in the browser. |
| **3. Option 2 plus APK sync** | Also the permission, the native bridge and new APKs. | The statement *"Nothing leaves the phone"* stops being true, and every family reinstalls. |

Student A's half is the same in options 2 and 3 and can be proven with fixture batches before any client exists.

---

### B. Student B (Copilot Scope: Offline Game Hosting & Client-Side Sync Queue)

**Baseline Already in Place (in the repository between 2026-09-23 and 2026-09-29):**

1. **Three Grade Apps (`pwa/tareas/primero/`, `segundo/`, `tercero/`)**:
   * One app per grade, seven modules each, one module per CNB mathematics competencia of that grade; every lesson is registered with a CNB content number of its module (`public/js/data/modules.js`).
   * "Look, listen, tap the answer": a wrong tap never ends a round, the child hears a hint and tries again.
   * Fonts, drawings and sounds are bundled and every path is relative, so the same `public/` folder runs on the appliance and inside the APK. No file in the three `public/` folders names an external address.
2. **Appliance Hosting (`backend/src/main.py`, `backend/src/api/captive.py`)**:
   * `REPO_MOUNTS` serves `/tareas/primero/`, `/tareas/segundo/`, `/tareas/tercero/` and `/descargas/` straight from the repository; the captive portal treats both prefixes as reserved.
   * `tests/api/test_repo_mounts.py`: each grade app answers with its relative assets, the download page lists the three grades, and an APK is served as an Android package.
3. **Offline Android Wrapper (`pwa/tareas/android/`)**:
   * One `Activity` with a `WebView` and one product flavor per grade; the lessons are packed from `../<grade>/public` at build time, and the phone's text-to-speech is exposed as `window.AndroidTTS`.
   * No service worker and no `INTERNET` permission.
4. **Family Download Page (`pwa/tareas/descargas/`)**: grade menu, install steps in Spanish and the APK links.
5. **Class Mode `apps` (`pwa/app/src/features/mode/`, [`GET`/`PUT /api/v1/mode`](../api/system.md#classroom-mode))**: the teacher picks "llevar a casa"; student phones show the grade menu (download the app or play it in the browser) with no login, and the classroom screen shows `tutorbox/descargas`.

**Not Started:**

* **Client-Side Error Logging**: no game writes an error event to `localStorage` or IndexedDB. Progress is the best star count per lesson (`kuk_progress_v1`, `kuk2_progress_v1`, `kuk3_progress_v1`).
* **Background Sync on AP Reconnection**: the only `fetch` in the three apps is the service worker's cache fill, which does not run on the appliance or in the APK.

---

## 3. Tuesday Jury Defense Package (Copilot B Defense Script)

* **Topic**: *"Opportunistic Synchronization: Data that survives disconnection"*
* **Presenter**: Student B (Copilot)

### Key Talking Points for the Jury:

1. **Offline-First Game Hosting and Caching Architecture**:
   * Can be shown today: one `public/` folder per grade, served by the appliance and packed into the APK, with nothing loaded from outside.
   * Why an APK and not an installable PWA: browsers run service workers only over HTTPS, and the appliance serves plain `http://tutorbox`.
2. **Client-Side Event Queuing and Deduplicated Background Synchronization**:
   * Nothing to show yet. It depends on the open decision in Section 2.A.
3. **Conceptual Error Alignment Across Quiz, Tutor and Games Modes**:
   * Can be argued today from the labels the quiz and the tutor already store (`quiz_session_votes.misconception`, `turn_logs.cnb_topic` and the taxonomy pair). The games column of that comparison is empty until events are ingested.
