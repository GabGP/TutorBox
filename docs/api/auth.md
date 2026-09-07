# Authentication & User Self-Service API Specification

Technical specification for user authentication, bearer session management, and self-service credential operations in **TutorBox**.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [REST API](README.md) › **Authentication & Users** • **Related:** [Staff Admin](staff.md) • [Database Schema](../database/README.md)

</div>

---

## Endpoint Overview

These endpoints manage user onboarding, session authentication, profile retrieval, and credential rotation (PIN and username changes).

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/auth/login` | Public (Rate-limited) | Authenticate user and issue bearer session token |
| `POST` | `/api/v1/auth/logout` | Bearer Token | Invalidate current active session |
| `POST` | `/api/v1/users/signup` | Public (Rate-limited) | Student self-service account registration |
| `GET` | `/api/v1/users/me` | Bearer Token | Retrieve caller profile and rotation status |
| `PATCH` | `/api/v1/users/me/pin` | Bearer Token | Rotate personal PIN (clears forced rotation flag) |
| `PATCH` | `/api/v1/users/me/username` | Bearer Token | Change username and release former username |

---

## Detailed Contracts

### <a id="post-auth-login"></a>`POST /api/v1/auth/login`

Authenticates a user using their username and 4–8 digit PIN. On success, issues a UUIDv4 session token persisted to the SQLite `sessions` table.

* **Authorization**: Public
* **Security & Guards**:
  * Protected by the Credential Lockout Rate Limiter (exponential backoff after repeated failed attempts).
  * Uses anti-oracle check ordering (constant-time verification behavior).
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

---

### <a id="post-auth-logout"></a>`POST /api/v1/auth/logout`

Invalidates the caller's active session token, setting `is_active = 0` in SQLite.

* **Authorization**: Bearer Token (`Authorization: Bearer <session_id>`)
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Logged out."
    }
    ```
  * `401 Unauthorized`: Missing, invalid, or already revoked session token.

---

### <a id="post-users-signup"></a>`POST /api/v1/users/signup`

Public registration allowing students to create their own accounts without administrative intervention.

* **Authorization**: Public
* **Security & Guards**:
  * Protected by the Global Sliding Window Rate Limiter.
  * Always assigns the default role `student`.
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
  * `422 Unprocessable Entity`: PIN is not 4–8 digits or username fails regex constraints.
  * `429 Too Many Requests`: Global signup rate limit exceeded.

---

### <a id="get-users-me"></a>`GET /api/v1/users/me`

Retrieves user profile metadata, role permissions, and PIN rotation status.

* **Authorization**: Bearer Token
* **Policy Note**: Allowed even when `must_change_pin == true` (included in the rotation allowlist).
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
  * `401 Unauthorized`: Invalid or expired session token.

---

### <a id="patch-users-me-pin"></a>`PATCH /api/v1/users/me/pin`

Changes the user's personal PIN. Verifies the current PIN, clears the `must_change_pin` flag, and invalidates all active sessions to force re-authentication.

* **Authorization**: Bearer Token
* **Policy Note**: Allowed during pending rotation.
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
  * `422 Unprocessable Entity`: `new_pin` equals `current_pin` or fails 4–8 digit validation.

---

### <a id="patch-users-me-username"></a>`PATCH /api/v1/users/me/username`

Updates the user's username. The previous username is recorded in `former_username` and freed for other students. Invalidates active sessions.

* **Authorization**: Bearer Token
* **Policy Note**: Gated by pending PIN rotation (must complete PIN change before changing username).
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
  * `403 Forbidden`: Forced PIN rotation pending.
  * `409 Conflict`: `new_username` is already taken.
  * `422 Unprocessable Entity`: `new_username` equals current username.

---

## Related Specifications

* **[API Gateway & Policies](README.md)**: RBAC matrix and anti-oracle check ordering.
* **[Staff Administration](staff.md)**: Teacher and administrator user management.
* **[Database Schema & ER Model](../database/README.md)**: `users` and `sessions` table specifications.
