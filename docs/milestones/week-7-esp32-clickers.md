# Week 7 Milestone: ESP32 Physical Clickers

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Milestones](roadmap.md) › **Week 7 Milestone** • **Related:** [Engineering Roadmap](roadmap.md) • [Clicker Transport](../architecture/esp32-clicker-transport.md) • [Clicker Protocol](../architecture/esp32-protocol.md) • [Devices API](../api/devices.md) • [Sessions API](../api/sessions.md) • [Week 6 Milestone](week-6-games-sync.md)

</div>

---

This document tracks the technical deliverables, architectural implementations, and quality metrics of the **Week 7 Milestone** by **Student A (Copilot: Backend Clicker Transport & Fleet Association Test)** and **Student B (Pilot: ESP32 Clicker Firmware, BLE Provisioner & Physical Assembly)**. It records the state of the repository on 2026-10-09.

---

## 1. Executive Summary & Verification Metrics

* **Theme**: *"One More Transport: Integrating hardware without redesigning the system"*
* **Status**: **Copilot (Student A) Backend Complete & Green · Pilot (Student B) Firmware, Provisioner and Assembly Not Started**
* **Backend Test Suite**: **2141 / 2141 passing tests** (95 new this week: 19 in `tests/core/db/`, 19 in `tests/api/staff/`, 35 test cases in `tests/api/devices/`, 16 for the vote label and the token scope in `tests/api/session/` and `tests/core/security/`, and 6 fleet tests in `tests/api/session/`).
* **Statement Coverage**: **100.00% statement coverage** across all 6,716 source statements (`pyproject.toml` enforces `--cov-fail-under=100`).
* **Linter & Formatter**: **0 errors, 0 warnings** (`pre-commit run --all-files` clean across all 7 hooks).
* **Modularity Compliance**: production modules are held to the 150-line ceiling by `tests/test_modularity_policy.py`. The largest new production module is `backend/src/api/devices/auth.py` (104 lines).
* **Acceptance Criteria Status**:
  * ⏳ **Live 10-question match with at least 10 physical ESP32 clickers and 0 lost votes**: pending hardware. Proven in CI today: 15 simulated clickers and 15 phones, through the real endpoints, play 5 rounds with zero lost votes (`test_session_fleet_hardware.py`). Not proven: a match with physical clickers, which waits for the firmware and the first batch.
  * ⏳ **Fleet benchmark report with connection limits and packet latency (ESP32 vs. web)**: pending hardware. The CI test has no radio, so it says nothing about router association limits or packet latency. The benchmark needs flashed clickers at the router.
* **Key Milestone Artifacts**:
  * **Clicker Secret**: `POST /api/v1/staff/devices/{device_id}/secret` issues a 32-character secret once. Only its SHA-256 digest is stored ([Devices API](../api/devices.md#post-staff-devices-secret)).
  * **Device Authentication**: `POST /api/v1/devices/auth` trades the secret for a bearer session of the assigned student, with its own lockout ([Devices API](../api/devices.md#post-devices-auth)).
  * **Token Scope**: a clicker's token can vote and nothing else. Every other endpoint refuses it with `403 "Clicker sessions can only vote."` ([Devices API](../api/devices.md#post-devices-auth)).
  * **Vote Label**: each vote is labelled `hardware` with the clicker's id, or `web`, from the caller's session. The request body cannot choose the label ([Sessions API](../api/sessions.md#post-session-vote)).
  * **Migration `015`**: three nullable columns and the partial index `idx_sessions_device_id` ([Migrations](../database/migrations.md#015-clicker-secret-and-session-device)).
  * **Revocation**: a clicker's sessions end when it is unassigned, reassigned, deleted, or given a new secret ([Clicker Token Revocation](../api/devices.md#clicker-token-revocation)).

---

## 2. Implemented Subsystems by Lead

### A. Student A (Copilot Scope: Backend Clicker Transport & Fleet Association Test)

**Design Decisions:**

1. **The server labels each vote from the session.** A clicker votes on the shared `POST /api/v1/session/{session_id}/vote` endpoint, not on a separate transport. The first design sent `transport_type` and `device_id` in the body, which let any client claim any label. Both fields are now ignored. A token issued to a clicker records `hardware` with that clicker's id, and any other token records `web`. The label follows the token, and the token follows the staff assignment.
2. **The secret is stored as a SHA-256 digest.** The secret is 128 random bits, so a fast hash is enough, the same reasoning the code gives for bearer tokens. The public device endpoint would otherwise run bcrypt on every request.
3. **One live token per clicker.** A new authentication revokes the clicker's earlier sessions, so the clicker holds one token at a time.
4. **A clicker's token can only vote.** The token votes as the assigned student, but it is not a login. `get_current_session`, which every endpoint depends on directly or through `require_roles`, refuses a session that was issued to a clicker. Only the vote endpoint asks for `get_voter_session`, which accepts it. The refusal is the default, so an endpoint added later refuses clickers without any extra code. A secret read out of a clicker's flash memory, or a token captured on the classroom Wi-Fi, therefore gives nothing but the votes that clicker could already cast.
5. **No separate driver class.** The roadmap item "backend `VoteTransport` driver" is built as the label in decision 1. The session engine has no hardware-specific code. The seam is the wire contract, as [Clicker Transport §5](../architecture/esp32-clicker-transport.md#5-abstract-votetransport-architecture-week-3--week-7-bridge) describes.

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
   * `get_voter_session` resolves any live session. `get_current_session` calls it and answers `403 "Clicker sessions can only vote."` when the session has a `device_id`. `submit_vote` is the only endpoint that depends on `get_voter_session`.
   * A revoked or expired clicker token still gets `401`, so the firmware's rule (on `401`, authenticate again) is unchanged.
   * `POST /api/v1/games/events` takes an optional login and never refuses a batch. Events sent with a clicker's token are stored with no student, like events sent with an expired login.
6. **Revocation (`backend/src/api/staff/device_pairing.py`, `devices.py`, `device_repository.py`)**:
   * A clicker's sessions end when it is unassigned, when it is assigned to a different student, when its student moves to another clicker, when it is deleted, and when it is given a new secret. Assigning the same student to the same clicker again revokes nothing. These events never end a phone login.
7. **Verification (`backend/tests/`)**:
   * `tests/core/db/test_device_repository.py` (14 tests) and `test_device_secret_migration_015.py` (5 tests): the repository functions, the new columns and index, and inserts that do not name the new columns.
   * `tests/api/staff/test_device_secret.py` (12 tests) and `test_device_revocation.py` (7 tests): the secret contract, the audit row, the log, and each revocation case.
   * `tests/api/devices/test_device_auth.py` and `test_device_auth_lockout.py`: the status codes and their detail strings, the anti-oracle symmetry, one live token, the lockout, and the log. The malformed-body test runs seven cases.
   * `tests/api/devices/test_device_token_scope.py` (12 test cases): a clicker's token is refused with `403` on the profile, the PIN change, the username change, logout, the three student tutor endpoints and a staff endpoint; the refused logout leaves the token able to vote; the refused PIN change leaves the PIN as it was; game events carry no student; and a phone login of the same student is still accepted.
   * `tests/api/session/test_session_hardware_vote.py` (8 tests), `test_transport.py` (2) and `tests/core/security/test_auth_session_device.py` (6): the label on each path, the first-press lock across transports, a revoked clicker's vote, and which of the three session dependencies accept a clicker's session.
   * The revocation rules and the token scope were checked by breaking each rule in the source and running these tests: ten deliberate breakages, each caught by at least one test.
   * Fleet, in CI: `tests/api/session/test_session_fleet_hardware.py` (6 tests, helpers in `fleet_support.py`) runs 15 simulated clickers and 15 phones through the real endpoints (register, assign, secret, authenticate, vote). Five rounds of 30 simultaneous votes store 150 rows, 75 `hardware` and 75 `web`, with none lost. The other tests cover 15 clickers pressing twice at once (one vote each), an unassigned clicker that stops voting while the other 14 continue, a reassigned clicker that votes as its new student after authenticating again, and the >51% rule with mixed transports (16 of 30 on one distractor speaks, 15 of 30 stays silent).

**Known Limits:**

* A student's own PIN or username change ends only the session it was made from, so a clicker's token keeps working after a phone change. A staff PIN reset ends it.
* The vote endpoint does not check a pending PIN rotation, as before this week. A student with a pending rotation can vote from a clicker or a phone.
* A `422` response repeats the value that was sent, as FastAPI does by default. Login does the same for a malformed PIN.
* The lockout counters are in memory, so a backend restart clears them.
* The fleet test is simulated. It proves the endpoints and the session rules, not the radio, the router's association limit or a clicker's latency.

**Interface for Student B (Firmware and Provisioner):**

| Call | Request | What the status means |
| :--- | :--- | :--- |
| `POST /api/v1/staff/devices/{device_id}/secret` (provisioner, teacher or admin token) | none | `200`: `{device_id, secret}`. Store the secret; it is returned once. `404 "Device not found."`: register the clicker first. `403`: the account is not a teacher or admin, or has a pending PIN change. |
| `POST /api/v1/devices/auth` | `{"device_id": "...", "secret": "<32 lowercase hex>"}` | `200`: `{session_id, username, device_id}`. Keep `session_id` in RAM and send it as `Authorization: Bearer`. `401 "Invalid device credentials."`: the secret is wrong or was replaced; provision again. `403 "Device is not assigned to any student."`: wait and authenticate again (the design retries every 30 s). `429`: locked out; wait. By default the lockout starts at 30 s and doubles up to 16 min. `422`: malformed packet. |
| `GET /api/v1/session/current` | none | `200`: the live match and its open round. `404 "No active session."`: no match yet. |
| `POST /api/v1/session/{session_id}/vote` (`session_id` from `GET /api/v1/session/current`) | `{"selected_option": "A"–"D"}`, optional `response_time_ms` | `200`: the vote is recorded. `401 "Invalid or expired session."`: authenticate again, once, then vote again. `409`: already voted in this round, or the round is not open. This is final; do not retry. `422`: the option is not `A` to `D`. `404`: the session or round is not found. |
| Any other endpoint, with the clicker's token | any | `403 "Clicker sessions can only vote."` Only the vote endpoint accepts the token. `GET /api/v1/session/current` is public and needs no token. |

The LED patterns are the ones in [Clicker Transport §6](../architecture/esp32-clicker-transport.md#6-visual-feedback--dual-led-state-machines) and [Clicker Protocol §3](../architecture/esp32-protocol.md#3-end-to-end-flow). This milestone does not change them.

---

### B. Student B (Pilot Scope: ESP32 Clicker Firmware, BLE Provisioner & Physical Assembly)

**Design Only (documents, no code in the repository):**

* BLE provisioning from the appliance: the GATT layout, the provisioning packet, and the one-clicker-at-a-time rule ([Clicker Protocol §4 and §7](../architecture/esp32-protocol.md#4-ble-provisioning-protocol)).
* The trust model, including the secret rotated on every provisioning ([Clicker Protocol §5](../architecture/esp32-protocol.md#5-trust-model-why-bluetooth-always-on-is-safe)).
* The firmware's provisioning routine, the NVS layout and the runtime loop ([Clicker Protocol §8](../architecture/esp32-protocol.md#8-esp32-firmware)).

**Not Started:**

* **ESP32 firmware**: there is no `firmware/` folder, so the PlatformIO project in Clicker Protocol §8 does not exist.
* **Jetson BLE provisioner**: there is no `infra/provisioner/` folder, and `infra/systemd/` has no provisioner unit.
* **Provisioner audit actions**: the design logs `device_provisioned` and `device_provision_failed`. Neither is in `VALID_ACTIONS` (`backend/src/core/db/audit.py`), so `record_audit` refuses them. They must be added with the provisioner.
* **Provisioner settings**: `.env.example` has no `CLICKER_*` or `PROVISIONER_*` entries.
* **Physical assembly and flashing** of the first clicker batch.
* **Real-device checks**: the bring-up checklist in [Clicker Protocol §10](../architecture/esp32-protocol.md#10-failure-modes--bring-up-checklist) has not been run on any clicker. No clicker has joined the router.

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
   * When the teacher unassigns or reassigns a clicker, its next vote is refused and it shows the red pattern. Giving it to another student needs no Bluetooth step: the clicker authenticates again with the secret it already holds and votes as the new student. Only a new secret or a deleted clicker needs provisioning again.
   * The first press locks per student per round across transports. A child who votes on a clicker and then on a phone gets `409`.
4. **Known limits, stated before the jury asks**:
   * A clicker's token can only vote, so a secret copied out of a clicker gives nothing but that clicker's votes. The vote endpoint does not check a pending PIN rotation.
   * The lockout counters are in memory.
