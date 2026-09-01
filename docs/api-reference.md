# REST API Reference & Contract Specification

Comprehensive technical specification and integration contracts for the **TutorBox** backend REST API.

<div align="center">

| 🏠 [TutorBox](../README.md) | 📚 [Docs](README.md) | ⚙️ [Backend](../backend/README.md) | 📱 [PWA](../pwa/README.md) | 🔌 [Infra](../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Docs** › **REST API Reference** • **Related:** [Database Schema](database-schema.md) • [Backend Guide](../backend/README.md)

</div>

---

## Table of Contents
- [1. System Overview & Base URL](#1-system-overview--base-url)
- [2. Authentication & Session Flow](#2-authentication--session-flow)
- [3. Role-Based Access Control (RBAC) Matrix](#3-role-based-access-control-rbac-matrix)
- [4. Security Policies & Guards](#4-security-policies--guards)
  - [A. Forced PIN Rotation Policy](#a-forced-pin-rotation-policy)
  - [B. Anti-Oracle Check Ordering](#b-anti-oracle-check-ordering)
  - [C. Rate Limiting Protection](#c-rate-limiting-protection)
- [5. Unified Error Response Format](#5-unified-error-response-format)
- [6. Detailed Endpoint Contracts](#6-detailed-endpoint-contracts)
  - [6.1 System & Health (`GET /health`)](#61-system--health)
  - [6.2 Authentication (`POST /api/v1/auth/login`, `POST /api/v1/auth/logout`)](#62-authentication)
  - [6.3 User Self-Service (`POST /api/v1/users/signup`, `GET /api/v1/users/me`, `PATCH /api/v1/users/me/pin`, `PATCH /api/v1/users/me/username`)](#63-user-self-service)
  - [6.4 Staff Administration (`GET /api/v1/staff/users`, `POST /api/v1/staff/users`, `POST /api/v1/staff/users/{user_id}/reset-pin`, `DELETE /api/v1/staff/users/{user_id}`, `POST /api/v1/staff/users/{user_id}/recover`)](#64-staff-administration)
  - [6.5 System Audit (`GET /api/v1/staff/audit-logs`)](#65-system-audit)
  - [6.6 Hardware Clicker & Device Fleet Management (`GET /api/v1/staff/devices`, `POST /api/v1/staff/devices`, `POST /api/v1/staff/devices/{device_id}/assign`, `POST /api/v1/staff/devices/{device_id}/unassign`, `DELETE /api/v1/staff/devices/{device_id}`)](#66-hardware-clicker--device-fleet-management)
  - [6.7 Quiz & Diagnostic Question Bank (`GET /api/v1/quiz/topics`, `GET /api/v1/quiz/schema`, `POST /api/v1/quiz/validate`, `POST /api/v1/quiz/generate`, `GET /api/v1/quiz/questions`, `GET /api/v1/quiz/questions/{id}`, `POST /api/v1/quiz/questions`, `DELETE /api/v1/quiz/questions/{id}`)](#67-quiz--diagnostic-question-bank)
- [Next Steps](#next-steps)

---

## <a id="1-system-overview--base-url"></a>1. System Overview & Base URL

The TutorBox API runs on the NVIDIA Jetson Orin Nano edge appliance and communicates with the React/Vite Progressive Web Application (PWA) over the local classroom WLAN/Ethernet network.

* **Base URL**: `http://<appliance-ip>:8000` (e.g., `http://127.0.0.1:8000` in local development)
* **API v1 Prefix**: `/api/v1` (e.g., `/api/v1/auth/login`, `/api/v1/quiz/generate`)
* **Unversioned Probes**: `/health`
* **Interactive Swagger UI**: `http://<appliance-ip>:8000/docs`
* **Raw OpenAPI JSON Schema**: `http://<appliance-ip>:8000/openapi.json`
* **Content-Type**: `application/json` (unless otherwise noted)

---

## <a id="2-authentication--session-flow"></a>2. Authentication & Session Flow

TutorBox uses stateful **Bearer Session Tokens** stored in the local SQLite database.

```mermaid
sequenceDiagram
    autonumber
    actor Client as PWA Client
    participant API as FastAPI Backend
    participant DB as SQLite DB

    Client->>API: POST /api/v1/auth/login {"username": "student1", "pin": "1234"}
    API->>DB: Query user & verify bcrypt hash
    API->>DB: INSERT INTO sessions (id, user_id, is_active) VALUES (uuid, id, 1)
    API-->>Client: 200 OK {"session_id": "<uuid4>", "username": "student1", "must_change_pin": false}

    Note over Client,API: Subsequent requests include Bearer Header
    Client->>API: GET /api/v1/users/me (Authorization: Bearer <uuid4>)
    API->>DB: Query sessions JOIN users WHERE id = uuid AND is_active = 1
    API-->>Client: 200 OK {"user_id": 1, "username": "student1", "role": "student", ...}

    Client->>API: POST /api/v1/auth/logout (Authorization: Bearer <uuid4>)
    API->>DB: UPDATE sessions SET is_active = 0 WHERE id = uuid
    API-->>Client: 200 OK {"detail": "Logged out."}
```

### Authorization Header Format
For all protected routes, the client must transmit the session token in the HTTP `Authorization` header:

```http
Authorization: Bearer <session_id>
```

---

## <a id="3-role-based-access-control-rbac-matrix"></a>3. Role-Based Access Control (RBAC) Matrix

TutorBox enforces strict role-based access across three user roles:
* **`student`**: Self-service learner account.
* **`teacher`**: Classroom supervisor (can manage students, other teachers, and hardware clickers).
* **`admin`**: System administrator (can manage all accounts, create/recover admins, view audit logs, and manage devices).

| Endpoint | Method | Public | Student | Teacher | Admin | Gated by Pending Rotation? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `/health` | `GET` | ✅ | ✅ | ✅ | ✅ | No (Public) |
| `/api/v1/users/signup` | `POST` | ✅ | ✅ | ✅ | ✅ | No (Public) |
| `/api/v1/auth/login` | `POST` | ✅ | ✅ | ✅ | ✅ | No (Public) |
| `/api/v1/auth/logout` | `POST` | ❌ | ✅ | ✅ | ✅ | No (Allowlist) |
| `/api/v1/users/me` | `GET` | ❌ | ✅ | ✅ | ✅ | No (Allowlist) |
| `/api/v1/users/me/pin` | `PATCH` | ❌ | ✅ | ✅ | ✅ | No (Allowlist) |
| `/api/v1/users/me/username` | `PATCH` | ❌ | ✅ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/staff/users` | `GET` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/staff/users` | `POST` | ❌ | ❌ | ✅ (student/teacher) | ✅ (any role) | **Yes (403 if rotation pending)** |
| `/api/v1/staff/users/{user_id}/reset-pin` | `POST` | ❌ | ❌ | ✅ (student/teacher) | ✅ (any role) | **Yes (403 if rotation pending)** |
| `/api/v1/staff/users/{user_id}` | `DELETE` | ❌ | ❌ | ✅ (student/teacher) | ✅ (any role) | **Yes (403 if rotation pending)** |
| `/api/v1/staff/users/{user_id}/recover` | `POST` | ❌ | ❌ | ✅ (student/teacher) | ✅ (any role) | **Yes (403 if rotation pending)** |
| `/api/v1/staff/audit-logs` | `GET` | ❌ | ❌ | ❌ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/staff/devices` | `GET` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/staff/devices` | `POST` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/staff/devices/{device_id}/assign` | `POST` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/staff/devices/{device_id}/unassign` | `POST` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/staff/devices/{device_id}` | `DELETE` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/quiz/topics` | `GET` | ✅ | ✅ | ✅ | ✅ | No (Public) |
| `/api/v1/quiz/schema` | `GET` | ✅ | ✅ | ✅ | ✅ | No (Public) |
| `/api/v1/quiz/validate` | `POST` | ✅ | ✅ | ✅ | ✅ | No (Public) |
| `/api/v1/quiz/generate` | `POST` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/quiz/questions` | `GET` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/quiz/questions/{id}` | `GET` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/quiz/questions` | `POST` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |
| `/api/v1/quiz/questions/{id}` | `DELETE` | ❌ | ❌ | ✅ | ✅ | **Yes (403 if rotation pending)** |



---

## <a id="4-security-policies--guards"></a>4. Security Policies & Guards

### <a id="a-forced-pin-rotation-policy"></a>A. Forced PIN Rotation Policy
* When a staff member resets an account's PIN or recovers an account, `must_change_pin` is set to `1` in SQLite.
* Upon login, the client receives `"must_change_pin": true`.
* **Allowlist Routes**: The user can **only** call `GET /api/v1/users/me`, `PATCH /api/v1/users/me/pin`, and `POST /api/v1/auth/logout`.
* **Gated Routes**: All other operational and administrative endpoints immediately reject the request with `403 Forbidden` (`{"detail": "PIN change required."}`).
* Once `PATCH /api/v1/users/me/pin` succeeds, `must_change_pin` is cleared to `0`.

### <a id="b-anti-oracle-check-ordering"></a>B. Anti-Oracle Check Ordering
To prevent timing or side-channel oracle attacks during credential modifications:
1. The backend **first** verifies the caller's `current_pin`. If incorrect, it immediately returns `401 Unauthorized`.
2. Only after `current_pin` is cryptographically validated does the backend compare whether `new_pin == current_pin` or `new_username == current_username` (returning `422 Unprocessable Entity`).

### <a id="c-rate-limiting-protection"></a>C. Rate Limiting Protection
* **Credential Lockout (`InMemoryRateLimiter`)**: 5 consecutive failed login/credential attempts result in a temporary lockout on the targeted username (returning `429 Too Many Requests`).
* **Registration Throttle (`SlidingWindowLimiter`)**: Global signup requests are capped to prevent brute-force storage exhaustion on edge hardware.

---

## <a id="5-unified-error-response-format"></a>5. Unified Error Response Format

All error responses return a standardized JSON object:

```json
{
  "detail": "Descriptive error explanation."
}
```

### Standard Status Codes
* **`200 OK`**: Request succeeded.
* **`201 Created`**: Resource created successfully.
* **`400 Bad Request`**: Malformed payload syntax.
* **`401 Unauthorized`**: Missing, invalid, or expired session token, or invalid username/PIN.
* **`403 Forbidden`**: Insufficient role privileges or forced PIN rotation required.
* **`404 Not Found`**: Target user ID does not exist or is soft-deleted.
* **`409 Conflict`**: Username collision or violation of the Last-Admin Guard.
* **`422 Unprocessable Entity`**: Validation failure (field regex, length, or new PIN equal to current PIN).
* **`429 Too Many Requests`**: Rate limit exceeded or account temporarily locked out.
* **`500 Internal Server Error`**: Unexpected backend failure.

---

## <a id="6-detailed-endpoint-contracts"></a>6. Detailed Endpoint Contracts

### <a id="61-system--health"></a>6.1 System & Health

#### `GET /health`
System and database diagnostic probe.

* **Authorization**: Public
* **Responses**:
  * `200 OK`:
    ```json
    {
      "status": "ok",
      "service": "TutorBox Backend",
      "database": "healthy"
    }
    ```

---

### <a id="62-authentication"></a>6.2 Authentication

#### `POST /api/v1/auth/login`
Authenticate a user with username and PIN to obtain a session token.

* **Authorization**: Public (Rate-limited)
* **Request Body**:
  ```json
  {
    "username": "student1",
    "pin": "1234"
  }
  ```
* **Responses**:
  * `200 OK`:
    ```json
    {
      "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "username": "student1",
      "status": "authenticated",
      "must_change_pin": false
    }
    ```
  * `401 Unauthorized`: Invalid credentials.
  * `422 Unprocessable Entity`: Username format or PIN digits invalid.
  * `429 Too Many Requests`: Account locked due to repeated failed attempts.

#### `POST /api/v1/auth/logout`
Invalidate the current caller's active session.

* **Authorization**: Bearer Token
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Logged out."
    }
    ```
  * `401 Unauthorized`: Missing, invalid, or already revoked session token.

---

### <a id="63-user-self-service"></a>6.3 User Self-Service

#### `POST /api/v1/users/signup`
Public student self-registration.

* **Authorization**: Public (Rate-limited)
* **Request Body**:
  ```json
  {
    "username": "maria_g",
    "pin": "5678"
  }
  ```
* **Responses**:
  * `201 Created`:
    ```json
    {
      "username": "maria_g",
      "role": "student"
    }
    ```
  * `409 Conflict`: Username is already taken.
  * `422 Unprocessable Entity`: Validation constraint violated.
  * `429 Too Many Requests`: Global signup rate limit exceeded.

#### `GET /api/v1/users/me`
Retrieve profile metadata for the authenticated user.

* **Authorization**: Bearer Token (Permitted during pending rotation)
* **Responses**:
  * `200 OK`:
    ```json
    {
      "user_id": 1,
      "username": "student1",
      "role": "student",
      "must_change_pin": false
    }
    ```
  * `401 Unauthorized`: Invalid or expired session.

#### `PATCH /api/v1/users/me/pin`
Change personal PIN. Clears forced rotation flag and invalidates the current session.

* **Authorization**: Bearer Token (Permitted during pending rotation)
* **Request Body**:
  ```json
  {
    "current_pin": "1234",
    "new_pin": "9876"
  }
  ```
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Credentials updated. Please sign in again."
    }
    ```
  * `401 Unauthorized`: Invalid `current_pin`.
  * `422 Unprocessable Entity`: `new_pin` equals `current_pin` or fails validation.

#### `PATCH /api/v1/users/me/username`
Change personal username. Frees the old username and invalidates the current session.

* **Authorization**: Bearer Token (Gated by pending rotation)
* **Request Body**:
  ```json
  {
    "current_pin": "1234",
    "new_username": "maria_new"
  }
  ```
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Credentials updated. Please sign in again."
    }
    ```
  * `401 Unauthorized`: Invalid `current_pin`.
  * `403 Forbidden`: PIN rotation pending.
  * `409 Conflict`: `new_username` is already taken.
  * `422 Unprocessable Entity`: `new_username` equals current username.

---

### <a id="64-staff-administration"></a>6.4 Staff Administration

#### `GET /api/v1/staff/users`
List accounts in the school roster.

* **Authorization**: Teacher, Admin
* **Query Parameters**:
  * `include_deleted` (`bool`, optional, default: `false`): If `true`, returns soft-deleted accounts.
* **Responses**:
  * `200 OK` (Active Roster):
    ```json
    {
      "users": [
        {
          "id": 1,
          "username": "student1",
          "role": "student",
          "created_at": "2026-08-27 10:00:00",
          "must_change_pin": false
        }
      ]
    }
    ```
  * `200 OK` (`include_deleted=true`):
    ```json
    {
      "users": [
        {
          "id": 2,
          "role": "student",
          "former_username": "student2",
          "deleted_at": "2026-08-27 12:30:00"
        }
      ]
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.

#### `POST /api/v1/staff/users`
Create a new user account.

* **Authorization**: Teacher (can create `student`, `teacher`), Admin (can create any role)
* **Request Body**:
  ```json
  {
    "username": "carlos_p",
    "pin": "1234",
    "role": "student"
  }
  ```
* **Responses**:
  * `201 Created`:
    ```json
    {
      "username": "carlos_p",
      "role": "student"
    }
    ```
  * `403 Forbidden`: Teacher attempting to create an admin account.
  * `409 Conflict`: Username already taken.

#### `POST /api/v1/staff/users/{user_id}/reset-pin`
Issue a random 6-digit temporary PIN and require rotation.

* **Authorization**: Teacher (targets `student`, `teacher`), Admin (targets any role)
* **Path Parameters**:
  * `user_id` (`integer`, required): Target user ID.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "username": "student1",
      "temporary_pin": "583921"
    }
    ```
  * `403 Forbidden`: Teacher attempting to reset an admin PIN.
  * `404 Not Found`: User not found or soft-deleted.

#### `DELETE /api/v1/staff/users/{user_id}`
Soft-delete an account, anonymize username, deactivate sessions, and retain educational logs.

* **Authorization**: Teacher (targets `student`, `teacher`), Admin (targets any role)
* **Path Parameters**:
  * `user_id` (`integer`, required): Target user ID.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Account deleted."
    }
    ```
  * `403 Forbidden`: Teacher attempting to delete an admin account.
  * `404 Not Found`: Target user ID not found or already deleted.
  * `409 Conflict`: Attempting to delete the last remaining admin.

#### `POST /api/v1/staff/users/{user_id}/recover`
Restore a soft-deleted account under a new username with a temporary PIN.

* **Authorization**: Teacher (targets `student`, `teacher`), Admin (targets any role)
* **Path Parameters**:
  * `user_id` (`integer`, required): Target user ID.
* **Request Body**:
  ```json
  {
    "username": "student2_restored"
  }
  ```
* **Responses**:
  * `200 OK`:
    ```json
    {
      "username": "student2_restored",
      "temporary_pin": "847291",
      "detail": "Account recovered. User must set a new PIN on next login."
    }
    ```
  * `403 Forbidden`: Teacher attempting to recover an admin account.
  * `404 Not Found`: Target is not soft-deleted or does not exist.
  * `409 Conflict`: Target recovery username is already taken.

---

### <a id="65-system-audit"></a>6.5 System Audit

#### `GET /api/v1/staff/audit-logs`
Read up to 500 append-only audit trail records.

* **Authorization**: Admin Only
* **Responses**:
  * `200 OK`:
    ```json
    {
      "logs": [
        {
          "id": 10,
          "actor_user_id": 3,
          "action": "pin_reset",
          "target_user_id": 1,
          "created_at": "2026-08-27 14:15:00"
        },
        {
          "id": 9,
          "actor_user_id": null,
          "action": "signup",
          "target_user_id": 5,
          "created_at": "2026-08-27 14:10:00"
        }
      ]
    }
    ```
  * `403 Forbidden`: Caller is not an admin.

---

### <a id="66-hardware-clicker--device-fleet-management"></a>6.6 Hardware Clicker & Device Fleet Management

#### `GET /api/v1/staff/devices`
List all registered physical ESP32 clickers with current student pairing info.

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

#### `POST /api/v1/staff/devices`
Register a new physical clicker identifier into the appliance fleet.

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

#### `POST /api/v1/staff/devices/{device_id}/assign`
Link a physical clicker to an active student user account.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `device_id` (`string`, required): Unique device identifier.
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
  * `422 Unprocessable Entity`: Target user is not a student account.

#### `POST /api/v1/staff/devices/{device_id}/unassign`
Unlink a physical clicker from any student.

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

#### `DELETE /api/v1/staff/devices/{device_id}`
Remove a physical clicker from the appliance fleet.

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

### <a id="67-quiz--diagnostic-question-bank"></a>6.7 Quiz & Diagnostic Question Bank

#### `GET /api/v1/quiz/topics`
Retrieve the full primary mathematics curriculum taxonomy including topics, subconcepts, and diagnostic misconception codes.

* **Authorization**: Public
* **Responses**:
  * `200 OK`:
    ```json
    [
      {
        "name": "arithmetic",
        "subconcepts": [
          {
            "name": "addition_subtraction",
            "misconceptions": [
              "sign_error",
              "borrowing_error",
              "alignment_error",
              "added_instead_of_subtracted"
            ]
          },
          {
            "name": "order_of_operations",
            "misconceptions": [
              "left_to_right_precedence",
              "addition_before_multiplication",
              "ignored_parentheses"
            ]
          }
        ]
      },
      {
        "name": "fractions",
        "subconcepts": [
          {
            "name": "addition_subtraction",
            "misconceptions": [
              "added_denominators",
              "ignored_common_denominator",
              "subtracted_denominators"
            ]
          }
        ]
      }
    ]
    ```

#### `GET /api/v1/quiz/schema`
Retrieve the canonical versioned JSON Schema (Draft 2020-12) for diagnostic quiz questions. Used by frontend PWAs, offline clickers, and sync engines for dynamic schema discovery and client-side payload validation.

* **Authorization**: Public
* **Responses**:
  * `200 OK`:
    ```json
    {
      "$defs": {
        "DistractorDetail": {
          "properties": {
            "misconception": {
              "description": "Slug of the diagnosed misconception",
              "maxLength": 100,
              "minLength": 2,
              "title": "Misconception",
              "type": "string"
            },
            "explanation": {
              "description": "Primary-school friendly explanation",
              "maxLength": 500,
              "minLength": 5,
              "title": "Explanation",
              "type": "string"
            }
          },
          "required": ["misconception", "explanation"],
          "title": "DistractorDetail",
          "type": "object"
        }
      },
      "properties": {
        "schema_version": {
          "default": "1.0.0",
          "description": "Contract schema version",
          "title": "Schema Version",
          "type": "string"
        },
        "topic": { "maxLength": 64, "minLength": 2, "title": "Topic", "type": "string" },
        "subconcept": { "maxLength": 64, "minLength": 2, "title": "Subconcept", "type": "string" },
        "question_text": { "maxLength": 500, "minLength": 5, "title": "Question Text", "type": "string" },
        "options": { "additionalProperties": { "type": "string" }, "title": "Options", "type": "object" },
        "correct_option": { "enum": ["A", "B", "C", "D"], "title": "Correct Option", "type": "string" },
        "distractors": { "additionalProperties": { "$ref": "#/$defs/DistractorDetail" }, "title": "Distractors", "type": "object" },
        "id": { "maxLength": 64, "minLength": 1, "title": "Id", "type": "string" }
      },
      "required": ["topic", "subconcept", "question_text", "options", "correct_option", "distractors", "id"],
      "title": "QuizQuestion",
      "type": "object",
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "$id": "https://tutorbox.local/schemas/v1/quiz_question.schema.json",
      "version": "1.0.0",
      "description": "Canonical versioned contract schema for TutorBox diagnostic multiple-choice quiz questions."
    }
    ```

#### `POST /api/v1/quiz/validate`
Execute deterministic SymPy validation on an arbitrary multiple-choice diagnostic item without persisting it.

* **Authorization**: Public
* **Request Body**:
  ```json
  {
    "question": {
      "id": "q_val_001",
      "topic": "pre_algebra",
      "subconcept": "one_step_equations",
      "question_text": "¿Cuál es el valor de x en la ecuación x + 4 = 10?",
      "options": {
        "A": "6",
        "B": "14",
        "C": "4",
        "D": "5"
      },
      "correct_option": "A",
      "distractors": {
        "B": {
          "misconception": "sign_flip_error",
          "explanation": "Sumaste 4 a 10 en vez de restar 4."
        },
        "C": {
          "misconception": "wrong_inverse_operation",
          "explanation": "Restaste 6 en vez de restar 4."
        },
        "D": {
          "misconception": "table_lookup_error",
          "explanation": "Error menor al calcular 10 - 4."
        }
      }
    }
  }
  ```
* **Responses**:
  * `200 OK` (Valid Math):
    ```json
    {
      "is_valid": true,
      "errors": [],
      "details": {
        "eval_mode": "equation",
        "target_solution": "6"
      }
    }
    ```
  * `200 OK` (Invalid Math):
    ```json
    {
      "is_valid": false,
      "errors": [
        "Correct option 'A' ('99') does not equal computed truth '6'"
      ],
      "details": {
        "eval_mode": "equation",
        "target_solution": "6"
      }
    }
    ```
  * `422 Unprocessable Entity`: JSON schema violation (missing distractor, invalid option key).

#### `POST /api/v1/quiz/generate`
Generate a new diagnostic question on-demand using the rejection and retry pipeline.

* **Authorization**: Teacher, Admin
* **Request Body**:
  ```json
  {
    "topic": "arithmetic",
    "subconcept": "addition_subtraction",
    "save_to_bank": true
  }
  ```
* **Responses**:
  * `200 OK`:
    ```json
    {
      "id": "q_gen_a1b2c3d4",
      "topic": "arithmetic",
      "subconcept": "addition_subtraction",
      "question_text": "¿Cuánto es 54 + 38?",
      "options": {
        "A": "82",
        "B": "16",
        "C": "92",
        "D": "812"
      },
      "correct_option": "C",
      "distractors": {
        "A": {
          "misconception": "alignment_error",
          "explanation": "Olvidaste sumar la decena que llevabas."
        },
        "B": {
          "misconception": "added_instead_of_subtracted",
          "explanation": "Restaste 54 - 38 en vez de sumarlos."
        },
        "D": {
          "misconception": "borrowing_error",
          "explanation": "Escribiste el 12 completo al lado de la suma de decenas."
        }
      },
      "source": "llm",
      "sympy_verified": true,
      "created_at": "2026-08-31 12:00:00"
    }
    ```
  * `403 Forbidden`: Caller is a student or has pending PIN rotation.
  * `422 Unprocessable Entity`: Invalid topic or subconcept slug.
  * `502 Bad Gateway`: SLM generation failed all retry attempts.

#### `GET /api/v1/quiz/questions`
Query and filter diagnostic questions from the question bank.

* **Authorization**: Teacher, Admin
* **Query Parameters**:
  * `topic` (`string`, optional): Filter by curriculum topic slug.
  * `subconcept` (`string`, optional): Filter by subconcept slug.
  * `limit` (`integer`, optional, default: `50`, min: `1`, max: `200`): Pagination limit.
  * `offset` (`integer`, optional, default: `0`, min: `0`): Pagination offset.
  * `include_deleted` (`bool`, optional, default: `false`): Include soft-deleted questions.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "questions": [
        {
          "id": "seed_arith_add_01",
          "topic": "arithmetic",
          "subconcept": "addition_subtraction",
          "question_text": "¿Cuánto es 54 + 38?",
          "options": {
            "A": "82",
            "B": "16",
            "C": "92",
            "D": "812"
          },
          "correct_option": "C",
          "distractors": {
            "A": {
              "misconception": "alignment_error",
              "explanation": "Olvidaste sumar la decena que llevabas."
            },
            "B": {
              "misconception": "added_instead_of_subtracted",
              "explanation": "Restaste 54 - 38 en vez de sumarlos."
            },
            "D": {
              "misconception": "borrowing_error",
              "explanation": "Escribiste el 12 completo al lado de la suma de decenas."
            }
          },
          "source": "seed",
          "sympy_verified": true,
          "created_at": "2026-08-31 10:00:00"
        }
      ],
      "total": 66
    }
    ```
  * `403 Forbidden`: Caller is a student or has pending PIN rotation.

#### `GET /api/v1/quiz/questions/{id}`
Fetch a single diagnostic question by its unique identifier.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `id` (`string`, required): Unique question identifier.
* **Responses**:
  * `200 OK`: Question JSON model.
  * `404 Not Found`: Question ID does not exist or is soft-deleted.

#### `POST /api/v1/quiz/questions`
Manually create a teacher-authored diagnostic question with deterministic SymPy verification.

* **Authorization**: Teacher, Admin
* **Request Body**:
  ```json
  {
    "id": "q_teacher_manual_01",
    "topic": "fractions",
    "subconcept": "addition_subtraction",
    "question_text": "¿Cuánto es 1/4 + 2/4?",
    "options": {
      "A": "3/4",
      "B": "3/8",
      "C": "2/8",
      "D": "1/2"
    },
    "correct_option": "A",
    "distractors": {
      "B": {
        "misconception": "added_denominators",
        "explanation": "Sumaste los denominadores 4+4=8 en vez de mantener el común denominador."
      },
      "C": {
        "misconception": "multiplied_only_numerators",
        "explanation": "Multiplicaste los numeradores y sumaste denominadores."
      },
      "D": {
        "misconception": "subtracted_denominators",
        "explanation": "Confundiste 3/4 con 1/2."
      }
    }
  }
  ```
* **Responses**:
  * `201 Created`: Created `QuizQuestionResponse`.
  * `403 Forbidden`: Caller is a student or has pending PIN rotation.
  * `409 Conflict`: Question with specified `id` already exists in the bank.
  * `422 Unprocessable Content`: Mathematical validation failure or schema/taxonomy error.

#### `DELETE /api/v1/quiz/questions/{id}`
Soft-delete a diagnostic question from the question bank while retaining telemetry integrity.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `id` (`string`, required): Question identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Question deleted."
    }
    ```
  * `403 Forbidden`: Caller is a student or has pending PIN rotation.
  * `404 Not Found`: Question not found or already deleted.

---

## Next Steps

* **[Database Schema Reference](database-schema.md)**: Explore the SQLite schema, table data dictionaries, and migration logs.
* **[Documentation Portal](README.md)**: Return to the documentation hub.
* **[Backend Developer Guide](../backend/README.md)**: Setup, local execution, and testing procedures.
