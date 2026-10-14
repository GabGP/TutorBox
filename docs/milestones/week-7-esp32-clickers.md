# Week 7 Milestone: ESP32 Physical Clickers

<div align="center">

| 🏠 [Utz'tutor](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Milestones](roadmap.md) › **Week 7 Milestone** • **Related:** [Engineering Roadmap](roadmap.md) • [Clicker Transport](../architecture/esp32-clicker-transport.md) • [Clicker Protocol](../architecture/esp32-protocol.md) • [Devices API](../api/devices.md) • [Sessions API](../api/sessions.md) • [Week 6 Milestone](week-6-games-sync.md)

</div>

---

This document tracks the technical deliverables, architectural implementations, and quality metrics of the **Week 7 Milestone** by **Student A (Copilot: Backend Clicker Transport & Fleet Association Test)** and **Student B (Pilot: ESP32 Clicker Firmware & Physical Assembly)**. In Week 7 Student A worked on both halves, and the BLE provisioner of the first design was dropped on 2026-10-13. It records the state of the repository on 2026-10-10; the firmware and provisioner parts and the backend test figures were updated on 2026-10-13.

---

## 1. Executive Summary & Verification Metrics

* **Theme**: *"One More Transport: Integrating hardware without redesigning the system"*
* **Status**: **Backend Complete & Green · Firmware Passing on a PC and Flashed to One ESP32, Bring-Up Checks Open · BLE Provisioner Dropped · Fleet Assembly Not Started**
* **Backend Test Suite**: **2755 / 2755 passing tests** on 2026-10-13 (98 new for the clickers this week: 19 in `tests/core/db/`, 22 in `tests/api/staff/`, 35 test cases in `tests/api/devices/`, 16 for the vote label and the token scope in `tests/api/session/` and `tests/core/security/`, and 6 fleet tests in `tests/api/session/`; plus 8 for the database lock fix, 57 for the lobby presence and 18 for the rule that only students hold a clicker, all below).
* **Frontend Test Suite**: **472 / 472 passing tests** in 74 files (`pnpm test` in `pwa/app/`; this week 95 new in 9 files for the teacher clicker screen and 73 new, with 8 new files, for the lobby's class list). `pnpm typecheck` and `pnpm build` are clean.
* **Firmware Test Suite**: **336 / 336 checks** in `firmware/clicker/hosttest/run_tests.sh`, and all 13 steps of `firmware/clicker/hosttest/e2e_test.py`, which runs the real sketch on a PC against the real backend. They need `g++` under Linux, macOS or WSL and are not part of CI. The PlatformIO build for the ESP32-C3 succeeds (60% of flash, 12% of RAM).
* **Statement Coverage**: **100.00% statement coverage** across all 7,011 source statements (`pyproject.toml` enforces `--cov-fail-under=100`).
* **Linter & Formatter**: **0 errors, 0 warnings** (`pre-commit run --all-files` clean across all 8 hooks; `ruff check` and `ruff format --check` clean over the scope CI uses).
* **Modularity Compliance**: production modules are held to the 150-line ceiling by `tests/test_modularity_policy.py`. The largest new production module is `backend/src/api/presence/store.py` (105 lines).
* **Acceptance Criteria Status**:
  * ⏳ **Live 10-question match with at least 10 physical ESP32 clickers and 0 lost votes**: pending hardware. Proven in CI today: 15 simulated clickers and 15 phones, through the real endpoints, play 5 rounds with zero lost votes (`test_session_fleet_hardware.py`). Not proven: a match with physical clickers, which waits for the first batch.
  * ⏳ **Fleet benchmark report with connection limits and packet latency (ESP32 vs. web)**: pending hardware. The CI test has no radio, so it says nothing about router association limits or packet latency. The benchmark needs flashed clickers at the router.
* **Key Milestone Artifacts**:
  * **Clicker Secret**: `POST /api/v1/staff/devices/{device_id}/secret` issues a 32-character secret once. Only its SHA-256 digest is stored ([Devices API](../api/devices.md#post-staff-devices-secret)).
  * **Device Authentication**: `POST /api/v1/devices/auth` trades the secret for a bearer session of the assigned student, with its own lockout ([Devices API](../api/devices.md#post-devices-auth)).
  * **Token Scope**: a clicker's token can vote and send the presence heartbeat, and nothing else. Every other endpoint refuses it with `403 "Clicker sessions can only vote."` ([Devices API](../api/devices.md#post-devices-auth)).
  * **Vote Label**: each vote is labelled `hardware` with the clicker's id, or `web`, from the caller's session. The request body cannot choose the label ([Sessions API](../api/sessions.md#post-session-vote)).
  * **Migration `015`**: three nullable columns and the partial index `idx_sessions_device_id` ([Migrations](../database/migrations.md#015-clicker-secret-and-session-device)).
  * **Revocation**: a clicker's sessions end when it is unassigned, reassigned, deleted, or given a new secret ([Clicker Token Revocation](../api/devices.md#clicker-token-revocation)).
  * **Setup State in the List**: `GET /api/v1/staff/devices` returns `secret_issued_at` for each clicker, so staff can see which clickers were never set up ([Devices API](../api/devices.md#get-staff-devices)).
  * **Teacher Clicker Screen**: the **Clickers** button in the `/maestro/` header opens the fleet in its own sheet, where a teacher adds, assigns, unassigns and deletes clickers ([PWA](../../pwa/README.md)).
  * **Lobby Presence**: phones and clickers send `POST /api/v1/presence/heartbeat` every 5 seconds, and the pre-game lobby lists the class from `GET /api/v1/presence/class`: who is connected, by phone or by clicker, who dropped, and each clicker's signal and battery ([Presence API](../api/presence.md)).

---

## 2. Implemented Subsystems by Lead

### A. Student A (Copilot Scope: Backend Clicker Transport & Fleet Association Test)

**Design Decisions:**

1. **The server labels each vote from the session.** A clicker votes on the shared `POST /api/v1/session/{session_id}/vote` endpoint, not on a separate transport. The first design sent `transport_type` and `device_id` in the body, which let any client claim any label. Both fields are now ignored. A token issued to a clicker records `hardware` with that clicker's id, and any other token records `web`. The label follows the token, and the token follows the staff assignment.
2. **The secret is stored as a SHA-256 digest.** The secret is 128 random bits, so a fast hash is enough, the same reasoning the code gives for bearer tokens. The public device endpoint would otherwise run bcrypt on every request.
3. **One live token per clicker.** A new authentication revokes the clicker's earlier sessions, so the clicker holds one token at a time.
4. **A clicker's token can only vote and send the presence heartbeat.** The token votes as the assigned student, but it is not a login. `get_current_session`, which every endpoint depends on directly or through `require_roles`, refuses a session that was issued to a clicker. Only the vote endpoint and the heartbeat ask for `get_voter_session`, which accepts it. The refusal is the default, so an endpoint added later refuses clickers without any extra code. A secret read out of a clicker's flash memory, or a token captured on the classroom Wi-Fi, therefore gives the votes that clicker could already cast and the ability to make it look connected in the lobby, and nothing else. The scope was vote-only until 2026-10-11, when the heartbeat was added.
5. **Presence comes from a heartbeat, not from the poll.** Phones and clickers wait by polling the public `GET /api/v1/session/current`, which identifies nobody. The lobby needs names, so each client sends an authenticated heartbeat as well, and the poll stays public. The state is kept in memory, as the tutor's roster is: it is live state, and it is rebuilt within seconds of a restart.
6. **No separate driver class.** The roadmap item "backend `VoteTransport` driver" is built as the label in decision 1. The session engine has no hardware-specific code. The seam is the wire contract, as [Clicker Transport §3](../architecture/esp32-clicker-transport.md#3-the-votetransport-seam) describes.

**Delivered Subsystems:**

1. **Migration and Repository (`backend/migrations/015_add_device_secret.sql`, `backend/src/core/db/device_repository.py`)**:
   * `devices.secret_hash`, `devices.secret_issued_at` and `sessions.device_id`, all nullable, plus the partial index `idx_sessions_device_id`. `sessions.device_id` has no foreign key.
   * The repository receives digests that its callers computed. It never sees a secret or a bearer token.
2. **Secret Endpoint (`backend/src/api/staff/device_secret.py`)**:
   * `POST /api/v1/staff/devices/{device_id}/secret` for teachers and admins returns `{device_id, secret}`. The secret is returned once. The audit log records `device_secret_issued`.
   * Issuing a secret revokes the clicker's active sessions, and the old secret is refused from then on.
3. **Device Authentication (`backend/src/api/devices/auth.py`, `schemas.py`)**:
   * `POST /api/v1/devices/auth` is public and is mounted at `/api/v1/devices`. It answers `200` with `session_id`, `username` and `device_id`.
   * An unknown device, a device with no secret and a wrong secret all get `401 "Invalid device credentials."`. An unassigned device gets `403 "Device is not assigned to any student."`, which is not counted as a failure.
   * The lockout uses the login limiter under the key `device:<device_id>@<address>`, so a clicker never shares a lockout with a username.
4. **Vote Label (`backend/src/api/session/transport.py`, `participant.py`, `schemas.py`, `backend/src/core/security/auth_session.py`)**:
   * `AuthContext` carries the `device_id` of the session it was issued to. `resolve_vote_transport` turns that into the label.
   * `CastVoteRequest` no longer has `transport_type` or `device_id`. A client that still sends them is not refused, and the fields are ignored.
   * The session engine in `backend/src/modes/quiz/session/` was not changed.
5. **Token Scope (`backend/src/core/security/auth_session.py`, `backend/src/api/session/participant.py`)**:
   * `get_voter_session` resolves any live session. `get_current_session` calls it and answers `403 "Clicker sessions can only vote."` when the session has a `device_id`. `submit_vote` and the presence heartbeat are the only endpoints that depend on `get_voter_session`.
   * A revoked or expired clicker token still gets `401`, so the firmware's rule (on `401`, authenticate again) is unchanged.
   * `POST /api/v1/games/events` takes an optional login and never refuses a batch. Events sent with a clicker's token are stored with no student, like events sent with an expired login.
6. **Revocation (`backend/src/api/staff/device_pairing.py`, `devices.py`, `user_change_role.py`, `device_repository.py`)**:
   * A clicker's sessions end when it is unassigned, when it is assigned to a different student, when its student moves to another clicker, when it is deleted, when it is given a new secret, and when its student becomes a teacher or an admin. Assigning the same student to the same clicker again revokes nothing. These events never end a phone login.
   * Only students hold a clicker. Assigning already refused a staff account. Since 2026-10-11 a student who becomes staff gives the clicker back (`release_clicker_of_user`: unassigned, sessions revoked, a `device_unassigned` audit row), and the clicker login reads a clicker whose account is not a student's as unassigned (`403`).
7. **Setup State in the List (`backend/src/api/staff/devices.py`, `schemas.py`)**:
   * `GET /api/v1/staff/devices` returns `secret_issued_at` for each clicker: the time its current secret was issued, or `null` when it has never had one. The secret and its digest are never returned.
8. **Teacher Clicker Screen (`pwa/app/src/features/clickers/`, `pwa/app/src/pages/teacher/TeacherHeader.tsx`, `TeacherView.tsx`)**:
   * A **Clickers** button in the teacher header opens the fleet in its own sheet, at every step and in every mode, so a clicker can be reassigned during a match. It is not part of the settings accordion.
   * Each row shows the clicker id in full, the student it votes as or `Sin alumno`, and `Sin configurar` while `secret_issued_at` is `null`. Swiping a row gives **Info**, **Editar** and **Eliminar**, as in the question bank. Tapping the id opens **Editar**. **Eliminar** asks for a two-second hold.
   * **Editar** lists the students with no clicker first, then the students who hold one, labelled with that clicker, because assigning moves them. The add form checks the id against the server's rule before sending it.
   * The screen uses the list, register, assign, unassign and delete endpoints. It never calls the secret endpoint and never shows a secret.
   * The server sends user ids as numbers and the roster type declares them as strings. The clicker code compares them in string form and sends `user_id` as a number.
9. **Lobby Presence (`backend/src/api/presence/`, `backend/src/core/db/class_roster_repository.py`, `pwa/app/src/features/presence/`, `pwa/app/src/pages/teacher/TeacherLobby.tsx`)**:
   * `POST /api/v1/presence/heartbeat` answers `204`. A clicker's token records the clicker under its id with the `rssi` and `battery_pct` it sends. A student's login records the phone and ignores the body. A staff login is accepted and recorded nowhere.
   * `GET /api/v1/presence/class`, for teachers and admins, lists every student with the status of their phone and of their clicker (`online` within 15 seconds of the last beat, `dropped` after that, `absent` when never heard from), the clicker's signal level and battery, and the clickers that have no student. The rules are pure functions in `status.py`; the store in `store.py` forgets an entry after 30 minutes.
   * The lobby no longer shows the user table that settings already has. It shows the class list: a count (`18 de 24 conectados`, with how many dropped), one row per student with a phone mark and a clicker mark, signal bars and a low-battery warning under 20% for clickers, and the clickers with no student. A phone that dropped, or a clicker that dropped or never joined, is marked **Desconectado**; how long ago is said once, in the student's status. **Administrar usuarios** opens settings on the users list, and **Asignar clickers** opens the Clickers sheet. Starting the match is never blocked by who is missing.
   * The student page sends the heartbeat every 5 seconds while a student is logged in for a quiz, and at once when the page becomes visible again. Tutor mode keeps its own ping.
   * A phone shows connected or dropped only: a browser cannot read the Wi-Fi signal. A clicker with no student has no token, so it cannot send a heartbeat and is listed with no status.
10. **Verification (`backend/tests/`, `pwa/app/src/`)**:
   * `tests/core/db/test_device_repository.py` (14 tests) and `test_device_secret_migration_015.py` (5 tests): the repository functions, the new columns and index, and inserts that do not name the new columns.
   * `tests/api/staff/test_device_secret.py` (12 tests) and `test_device_revocation.py` (7 tests): the secret contract, the audit row, the log, and each revocation case.
   * `tests/api/staff/test_device_list_secret_state.py` (3 tests): the list shows `null` before a secret is issued and the stored time after, and it never carries the secret or its digest.
   * `tests/api/devices/test_device_auth.py` and `test_device_auth_lockout.py`: the status codes and their detail strings, the anti-oracle symmetry, one live token, the lockout, and the log. The malformed-body test runs seven cases.
   * `tests/api/devices/test_device_token_scope.py` (14 test cases): a clicker's token is refused with `403` on the profile, the PIN change, the username change, logout, the three student tutor endpoints, a staff endpoint and the class view; the heartbeat accepts it; the refused logout leaves the token able to vote; the refused PIN change leaves the PIN as it was; game events carry no student; and a phone login of the same student is still accepted.
   * `tests/api/session/test_session_hardware_vote.py` (8 tests), `test_transport.py` (2) and `tests/core/security/test_auth_session_device.py` (6): the label on each path, the first-press lock across transports, a revoked clicker's vote, and which of the three session dependencies accept a clicker's session.
   * The revocation rules and the token scope were checked by breaking each rule in the source and running these tests: ten deliberate breakages, each caught by at least one test.
   * Teacher clicker screen: 95 tests in `pwa/app/src/features/clickers/__tests__/` (8 files) and `pwa/app/src/pages/teacher/__tests__/TeacherClickers.test.tsx`. They cover the API client, the id rule, the dates, the row and its armed delete, the list, the add form, the two sheets, each error message, numeric and string user ids, and the header button. 42 deliberate breakages of the screen's source were each caught by at least one test.
   * Teacher clicker screen, in a browser: the built page was driven in headless Chrome at 360 px against a real backend with an empty database (add, invalid and duplicate id, assign, move a student between clickers, unassign, Info, swipe, hold to delete, Escape). The header fits with the new button, the id is never cut off, the armed row keeps its height, and no request goes to the secret endpoint. A mouse drag at desktop width opens the row's actions without opening **Editar**.
   * Database lock after a refused duplicate, found while driving the clicker screen and fixed: a `409` for a duplicate clicker id or username left the write lock held, so the next writes (a login, an assignment, a vote) waited 5 s and failed with `500`. `get_db` (`backend/src/core/db/database.py`) now rolls back before it closes. `tests/api/test_writes_after_refused_duplicate.py` (5 tests, one for each endpoint that refuses a duplicate) and 3 tests in `tests/core/db/test_database.py` cover it; all 5 fail without the rollback. Checked against a running server too: a login right after each refused duplicate answers `200`.
   * Lobby presence, backend: `tests/api/presence/` (49 tests: the store on a fake clock, the status rules at their edges, the heartbeat, the class view, and 15 clickers plus 15 phones all reported online) and `tests/core/db/test_class_roster_repository.py` (6 tests).
   * Lobby presence, frontend: 73 tests, in `pwa/app/src/features/presence/__tests__/` (6 files), `TeacherViewLobby.test.tsx`, `StudentViewPresence.test.tsx`, and new cases in `TeacherLobby.test.tsx` and `SettingsView.test.tsx`. They cover the API client, both hooks with fake timers, the labels, the row, the list, when the student page sends the heartbeat, and the two lobby buttons.
   * Lobby presence, against a running server: three simulated clickers and two phones sent heartbeats over HTTP to a backend with a scratch database. The class view reported them `online`, a clicker and a phone that stopped as `dropped` after 15 seconds with the seconds since their last beat, signal `good`, `fair` and `weak` for -55, -70 and -82 dBm, and the fourth clicker, which had no student, as unassigned. The built lobby was then photographed in a headless browser at 360 px, where it has no horizontal scroll, and at 1100 px: every status is readable as text, and both buttons open the right sheet.
   * Clickers held by students only, found and fixed on 2026-10-11: promoting a student to teacher left their clicker assigned, its token kept voting under the teacher's account, and the clicker login issued it new tokens. `tests/api/staff/test_user_role_change_clicker.py` (9 test cases), `tests/core/db/test_device_repository_release.py` (7) and one new test with two cases in `tests/api/devices/test_device_auth.py` cover it: the clicker is unassigned and its token refused for a new teacher and a new admin, the clicker cannot authenticate again, the promoted account's phone login and other students' clickers are untouched, a change to the same role keeps everything, and the audit row. Seven of these failed before the fix.
   * Fleet, in CI: `tests/api/session/test_session_fleet_hardware.py` (6 tests, helpers in `fleet_support.py`) runs 15 simulated clickers and 15 phones through the real endpoints (register, assign, secret, authenticate, vote). Five rounds of 30 simultaneous votes store 150 rows, 75 `hardware` and 75 `web`, with none lost. The other tests cover 15 clickers pressing twice at once (one vote each), an unassigned clicker that stops voting while the other 14 continue, a reassigned clicker that votes as its new student after authenticating again, and the >51% rule with mixed transports (16 of 30 on one distractor speaks, 15 of 30 stays silent).

**Known Limits:**

* A student's own PIN or username change ends only the session it was made from, so a clicker's token keeps working after a phone change. A staff PIN reset ends it.
* The vote endpoint does not check a pending PIN rotation, as before this week. A student with a pending rotation can vote from a clicker or a phone.
* A `422` response repeats the value that was sent, as FastAPI does by default. Login does the same for a malformed PIN.
* The lockout counters are in memory, so a backend restart clears them.
* The fleet test is simulated. It proves the endpoints and the session rules, not the radio, the router's association limit or a clicker's latency.
* Presence is kept in memory. A backend restart empties it, and it fills again as clients beat. The firmware sends the heartbeat, and its end-to-end test on a PC sees the clicker online in the class view. No real clicker has sent one yet.
* A phone whose screen locks stops beating, so it shows as dropped. That is accurate for voting, but the lobby cannot tell a locked phone from one that left the room.
* A clicker that was already assigned to a teacher or an admin before 2026-10-11 is not cleaned up by a migration. It gets no new token, and a token it already holds expires within 12 hours, but the Clickers screen shows it with that account until a teacher unassigns it.
* The teacher clicker screen was checked in a desktop browser at phone size, not on a phone. With a row's actions swiped open and nothing else open, Escape closes the whole Clickers sheet. A clicker row is about 104 px tall, so a phone shows four or five clickers at a time.

**Interface for the Firmware (the firmware calls exactly these since 2026-10-13):**

| Call | Request | What the status means |
| :--- | :--- | :--- |
| `POST /api/v1/staff/devices/{device_id}/secret` (USB setup, teacher or admin token) | none | `200`: `{device_id, secret}`. Store the secret; it is returned once. `404 "Device not found."`: register the clicker first. `403`: the account is not a teacher or admin, or has a pending PIN change. |
| `POST /api/v1/devices/auth` | `{"device_id": "...", "secret": "<32 lowercase hex>"}` | `200`: `{session_id, username, device_id}`. Keep `session_id` in RAM and send it as `Authorization: Bearer`. `401 "Invalid device credentials."`: the secret is wrong or was replaced; do the USB setup again, and do not ask again with the same secret. `403 "Device is not assigned to any student."`: wait and authenticate again (the firmware asks every 5 s). `429`: locked out; wait. By default the lockout starts at 30 s and doubles up to 16 min. `422`: malformed body. |
| `GET /api/v1/session/current` | none | `200`: the live match and its open round. `404 "No active session."`: no match yet. |
| `POST /api/v1/session/{session_id}/vote` (`session_id` from `GET /api/v1/session/current`) | `{"selected_option": "A"–"D"}`, optional `response_time_ms` | `200`: the vote is recorded. `401 "Invalid or expired session."`: authenticate again, once, then vote again. `409`: already voted in this round, or the round is not open. This is final; do not retry. `422`: the option is not `A` to `D`. `404`: the session or round is not found. |
| `POST /api/v1/presence/heartbeat`, every 5 seconds while a token is held | `{"rssi": -58, "battery_pct": 88}`, both optional | `204`: recorded; the lobby shows the clicker as connected for the next 15 seconds. `401`: authenticate again; if that answers `403`, drop the token and show the unassigned pattern. `422`: `rssi` outside -120 to 0 or `battery_pct` outside 0 to 100. |
| Any other endpoint, with the clicker's token | any | `403 "Clicker sessions can only vote."` Only the vote endpoint and the heartbeat accept the token. `GET /api/v1/session/current` is public and needs no token. |

The light patterns are in [Clicker Firmware §8](../../firmware/clicker/README.md#8-what-the-light-means).

---

### B. Student B (Pilot Scope: ESP32 Clicker Firmware & Physical Assembly)

In Week 7 Student A worked on this half too.

**Built:**

* **ESP32 firmware** in `firmware/clicker/` (ESP32-C3 Super Mini, Arduino framework). It was first committed on 2026-10-10 against `/api/v1/clicker/*` endpoints that are no longer in the backend. On 2026-10-13 it was ported to the interface above, with no backend change: it logs in with `POST /api/v1/devices/auth`, polls `GET /api/v1/session/current`, votes on `POST /api/v1/session/{session_id}/vote` and sends `POST /api/v1/presence/heartbeat` ([Clicker Firmware](../../firmware/clicker/README.md), [Clicker Protocol §8](../architecture/esp32-protocol.md#8-esp32-firmware)).
* **USB setup link**: the clicker takes its device secret as one line on its USB serial port and keeps it in flash ([Clicker Protocol §8.2](../architecture/esp32-protocol.md#82-usb-setup-link)). The clicker no longer makes up its own secret.
* **Firmware tests on a PC**: 336 unit checks, and an end-to-end run of the real sketch against the real backend (`firmware/clicker/hosttest/`). The end-to-end run covers the empty flash, the USB setup, the assignment, the class view, three questions, a double press, Wi-Fi loss, a backend outage, an unassignment, a power cycle and a replaced secret.
* **First build and upload for the board** (2026-10-13): firmware 2.0.0 builds with PlatformIO (`espressif32` 7.1.3, Arduino core 2.0.17) and was uploaded to one ESP32-C3 Super Mini over USB.

**Dropped or Removed on 2026-10-13:**

* **Jetson BLE provisioner**, and the Bluetooth half of the firmware ([Clicker Protocol §4 and §7](../architecture/esp32-protocol.md#4-ble-provisioning-protocol)). The Wi-Fi name and password are compiled into the firmware, and the secret arrives over USB. There is no `infra/provisioner/` folder, and the audit actions and the settings the provisioner needed were never added.
* **`tools/clickers/clickers.py`**, a command-line tool written for the removed `/api/v1/clicker/*` endpoints. The **Clickers** screen on `/maestro/` adds, assigns, unassigns and deletes clickers, and the fleet test in CI replaced its simulator. Its bulk assignment from a CSV file has no replacement.

**Not Started:**

* **A tool for the USB setup.** Today a person issues the secret in Swagger and types it in the Serial Monitor.
* **Physical assembly and flashing** of the first clicker batch. One clicker is wired on a bench (2026-10-13), without its charger.
* **Real-device checks**: one clicker is flashed, and the bring-up checklist in [Clicker Protocol §10](../architecture/esp32-protocol.md#10-failure-modes--bring-up-checklist) has not been recorded for it. No result on the board (joining the router, the USB setup, a counted vote) is written down yet.

---

## 3. Tuesday Jury Defense Package (Copilot A Defense Script)

* **Topic**: *"One More Transport: Integrating hardware without redesigning the system"*
* **Presenter**: Student A (Copilot)

### Key Talking Points for the Jury:

1. **Modularity: the session engine did not change**:
   * A clicker is a new way to obtain a student's token. After it authenticates with its secret, it votes on the same endpoint as a phone, so the server needs no new vote path.
   * The vote endpoint asks the session for its label. No file under `backend/src/modes/` changed this week.
2. **Association limits and latency: not measured yet**:
   * The CI fleet test shows that the session logic holds with 15 clickers and 15 phones: zero lost votes, and one vote per student per round.
   * The radio is not in the test. The fleet benchmark on hardware is the open item, and this defense does not quote a latency figure.
3. **Reliability and classroom ergonomics**:
   * When the teacher unassigns or reassigns a clicker, its heartbeat is refused within 5 seconds, it logs in again, and it shows the unassigned light. Giving it to another student needs no cable: the clicker authenticates again with the secret it already holds and votes as the new student. Only a new secret or a deleted clicker needs the USB setup again.
   * The first press locks per student per round across transports. A child who votes on a clicker and then on a phone gets `409`.
4. **Known limits, stated before the jury asks**:
   * A clicker's token can only vote and send the presence heartbeat, so a secret copied out of a clicker gives nothing but that clicker's votes and its line in the lobby. The vote endpoint does not check a pending PIN rotation.
   * The lockout counters are in memory.
