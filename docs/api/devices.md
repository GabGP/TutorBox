# Hardware Clicker & Device Fleet API Specification

Technical specification for physical ESP32 clicker registration, inventory management, and student pairing in **TutorBox**.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [REST API](README.md) › **Hardware Devices** • **Related:** [Staff Admin](staff.md) • [Clicker Transport](../architecture/esp32-clicker-transport.md)

</div>

---

## Endpoint Overview

These endpoints govern the appliance's hardware inventory, allowing teachers and administrators to register physical 4-button ESP32 clickers and assign them to specific student accounts for classroom voting. A clicker proves itself with a secret that staff issue to it, and trades that secret for a login session of its assigned student at the public `POST /api/v1/devices/auth` endpoint.

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/staff/devices` | Teacher, Admin | List all registered clickers and student assignments |
| `POST` | `/api/v1/staff/devices` | Teacher, Admin | Register a new clicker hardware ID into the fleet |
| `POST` | `/api/v1/staff/devices/{device_id}/assign` | Teacher, Admin | Pair a physical clicker to a student account |
| `POST` | `/api/v1/staff/devices/{device_id}/unassign` | Teacher, Admin | Unpair a physical clicker from any student |
| `POST` | `/api/v1/staff/devices/{device_id}/secret` | Teacher, Admin | Issue a new secret for a clicker; its active sessions are revoked |
| `DELETE` | `/api/v1/staff/devices/{device_id}` | Teacher, Admin | Remove a clicker identifier from the fleet |
| `POST` | `/api/v1/devices/auth` | Public | Trade a clicker's secret for a login session of its assigned student |

---

## Detailed Contracts

### <a id="get-staff-devices"></a>`GET /api/v1/staff/devices`

List all registered physical clickers, their creation timestamps, and current assigned student metadata.

* **Authorization**: Teacher, Admin
* **Responses**:
  * `200 OK`:
    ```json
    {
      "devices": [
        {
          "device_id": "1",
          "assigned_user_id": 12,
          "assigned_username": "juan_p",
          "created_at": "2026-08-29 14:00:00"
        },
        {
          "device_id": "ESP32_02",
          "assigned_user_id": null,
          "assigned_username": null,
          "created_at": "2026-08-29 14:05:00"
        }
      ]
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.

---

### <a id="post-staff-devices"></a>`POST /api/v1/staff/devices`

Registers a new physical clicker identifier into the appliance fleet.

* **Authorization**: Teacher, Admin
* **Request Body**:
  ```json
  {
    "device_id": "1"
  }
  ```
* **Responses**:
  * `201 Created`:
    ```json
    {
      "device_id": "1",
      "assigned_user_id": null,
      "assigned_username": null,
      "created_at": "2026-08-29 14:00:00"
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.
  * `409 Conflict`: `device_id` is already registered.
  * `422 Unprocessable Entity`: `device_id` is empty or invalid format.

---

### <a id="post-staff-devices-assign"></a>`POST /api/v1/staff/devices/{device_id}/assign`

Links a physical clicker to an active student user account. When the clicker's student changes, or the student leaves another clicker, the clicker sessions of the affected clickers are revoked (see [Clicker Token Revocation](#clicker-token-revocation)).

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `device_id` (`string`, required): Unique device identifier (e.g., `"1"`, `"ESP32_01"`).
* **Request Body**:
  ```json
  {
    "user_id": 12
  }
  ```
* **Responses**:
  * `200 OK`:
    ```json
    {
      "device_id": "1",
      "assigned_user_id": 12,
      "assigned_username": "juan_p"
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.
  * `404 Not Found`: Device or student account not found.
  * `422 Unprocessable Entity`: Target user account is not a student.

---

### <a id="post-staff-devices-unassign"></a>`POST /api/v1/staff/devices/{device_id}/unassign`

Unlinks a physical clicker from its currently paired student, setting `assigned_user_id = NULL`. It also revokes the clicker's active sessions, so its next vote is refused with `401`.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `device_id` (`string`, required): Unique device identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Device unassigned successfully."
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.
  * `404 Not Found`: Device not found.

---

### <a id="delete-staff-devices"></a>`DELETE /api/v1/staff/devices/{device_id}`

Removes a physical clicker identifier from the appliance database completely. Its active sessions are revoked first.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `device_id` (`string`, required): Unique device identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Device removed from fleet."
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.
  * `404 Not Found`: Device not found.

---

### <a id="post-staff-devices-secret"></a>`POST /api/v1/staff/devices/{device_id}/secret`

Issues a new secret for a physical clicker. The clicker sends this secret to `POST /api/v1/devices/auth`. A new secret replaces the old one at once, so the old one is refused from then on.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `device_id` (`string`, required): Unique device identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "device_id": "ESP32-A4CF12",
      "secret": "3f9c2a8e6b1d4c7f0a5e9d3b8c2f6a1e"
    }
    ```
  * `401 Unauthorized`: `"Missing or malformed Authorization header."` when no bearer token is sent; `"Invalid session token."` when the token is not a UUID; `"Invalid or expired session."` for an unknown, revoked or expired token.
  * `403 Forbidden`: `"Insufficient permissions."` for a student; `"PIN change required."` while a PIN rotation is pending.
  * `404 Not Found`: `"Device not found."`.
* **Notes**:
  * The secret is 32 lowercase hex characters (16 random bytes) and is returned once. The database keeps only its SHA-256 digest (`devices.secret_hash`) and the time it was issued (`devices.secret_issued_at`).
  * Issuing a secret revokes the clicker's active sessions. A clicker that was logged in must authenticate again with the new secret.
  * An unassigned clicker can be issued a secret.
  * The audit log records `device_secret_issued`, with the caller as actor and the clicker's assigned student as target. The target is empty when the clicker is unassigned.

---

### <a id="post-devices-auth"></a>`POST /api/v1/devices/auth`

A clicker has no PIN. It trades its secret for a login session of the student it is assigned to. The endpoint is public: it takes no bearer token, and it is rate-limited per device and address (see **Lockout** below).

* **Authorization**: Public
* **Request Body**:
  ```json
  {
    "device_id": "ESP32-A4CF12",
    "secret": "3f9c2a8e6b1d4c7f0a5e9d3b8c2f6a1e"
  }
  ```
  * `device_id` (`string`, required): 1 to 32 characters from `A-Z`, `a-z`, `0-9`, `_`, `.` and `-`.
  * `secret` (`string`, required): exactly 32 lowercase hex characters.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "username": "ana",
      "device_id": "ESP32-A4CF12"
    }
    ```
    `session_id` is a bearer token of the assigned student, sent as `Authorization: Bearer <session_id>`. The database keeps only its digest.
  * `401 Unauthorized`: `"Invalid device credentials."` An unknown device, a device that has no secret, and a wrong secret all get this same response.
  * `403 Forbidden`: `"Device is not assigned to any student."` The secret is right, but the clicker is unassigned or its student's account is deleted. This is not counted as a failed attempt, so a clicker waiting for the teacher can retry.
  * `422 Unprocessable Entity`: the body breaks the rules above. The response lists each invalid field and repeats the value sent, as FastAPI does by default (login does the same for a malformed PIN).
  * `429 Too Many Requests`: `"Too many failed login attempts. Please try again later."`
* **Notes**:
  * **Lockout**: each wrong secret counts against the key `device:<device_id>@<address>`, where `<address>` is the client address, as for login. After `AUTH_MAX_ATTEMPTS` wrong secrets (5 in `.env.example`) the key is locked for `AUTH_LOCKOUT_SECONDS` (30 in `.env.example`). Each later lockout lasts twice as long as the one before, up to 16 minutes. A locked device gets `429` even with the right secret. A successful authentication clears the count. The key never shares a lockout with a username. The counters are kept in memory, so a backend restart clears them.
  * **One live token**: a successful authentication revokes the clicker's earlier sessions, so a clicker holds one token at a time.
  * **Expiry**: the token expires 12 hours after it was issued (`SESSION_TTL_HOURS`), like any login. The clicker authenticates again when a vote returns `401`.
  * **Full student session**: the token is an ordinary student session. Every endpoint that accepts a student's token accepts it.
  * The vote endpoint labels a vote cast with this token as `hardware`, with the clicker's `device_id`. See [Sessions API](sessions.md#post-session-vote).
  * Neither the secret nor the token is written to the logs.

---

## <a id="clicker-token-revocation"></a>Clicker Token Revocation

A clicker's active sessions, the ones issued to it by `POST /api/v1/devices/auth`, are revoked when:

* the clicker is unassigned (`POST /api/v1/staff/devices/{device_id}/unassign`);
* the clicker is assigned to a different student;
* its student is moved to another clicker, which revokes the clicker the student left;
* the clicker is deleted (`DELETE /api/v1/staff/devices/{device_id}`);
* a new secret is issued (`POST /api/v1/staff/devices/{device_id}/secret`).

After a revocation the clicker's next vote is refused with `401`. When it authenticates again it gets `403` while it has no student, a new session for the student it has now, or `401` when its secret was replaced or the clicker was deleted.

Assigning the same student to the same clicker again revokes nothing. These events never end a phone or browser login, including a phone login of the same student. A student's own PIN or username change ends only the session it was made from. A staff PIN reset, or the deletion of the student's account, ends all of the student's sessions, the clicker's included.

---

## Related Specifications

* **[ESP32 Clicker Transport Architecture](../architecture/esp32-clicker-transport.md)**: Hardware schematics, pairing flow, and LED state machines.
* **[ESP32 Clicker Protocol](../architecture/esp32-protocol.md)**: The provisioning design the secret belongs to. Its §6 describes the endpoints as built.
* **[Database Schema & ER Model](../database/README.md)**: `devices` table specifications and indexes.
* **[Quiz Match & Voting Sessions](sessions.md)**: How a clicker's vote is labelled and stored.
