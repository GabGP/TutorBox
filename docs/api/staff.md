# Staff Administration & Audit API Specification

Technical specification for school roster administration, user lifecycle management, and append-only security audit logging in **TutorBox**.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [REST API](README.md) › **Staff Administration** • **Related:** [Authentication](auth.md) • [Device Management](devices.md)

</div>

---

## Endpoint Overview

Staff administration endpoints allow teachers and system administrators to manage classroom accounts, recover deleted users, reset forgotten PINs, and inspect security audit logs.

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/staff/users` | Teacher, Admin | List accounts in the school roster |
| `POST` | `/api/v1/staff/users` | Teacher, Admin | Create a new user account |
| `POST` | `/api/v1/staff/users/{user_id}/reset-pin` | Teacher, Admin | Issue temporary random PIN and enforce rotation |
| `DELETE` | `/api/v1/staff/users/{user_id}` | Teacher, Admin | Soft-delete an account and free username |
| `POST` | `/api/v1/staff/users/{user_id}/recover` | Teacher, Admin | Restore soft-deleted account under new username |
| `GET` | `/api/v1/staff/audit-logs` | Admin Only | Read append-only security audit log trails |

---

## Detailed Contracts

### <a id="get-staff-users"></a>`GET /api/v1/staff/users`

List user accounts in the school roster. Teachers can view students and teachers; admins can view all accounts.

* **Authorization**: Teacher, Admin
* **Query Parameters**:
  * `include_deleted` (`bool`, optional, default: `false`): If `true`, includes soft-deleted user records.
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

---

### <a id="post-staff-users"></a>`POST /api/v1/staff/users`

Creates a new user account administratively. Teachers may create `student` or `teacher` accounts; only admins may create `admin` accounts.

* **Authorization**: Teacher (targets `student`, `teacher`), Admin (targets any role)
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
  * `403 Forbidden`: Teacher attempting to create an `admin` account.
  * `409 Conflict`: Username already taken.

---

### <a id="post-staff-users-reset-pin"></a>`POST /api/v1/staff/users/{user_id}/reset-pin`

Issues a cryptographically random 6-digit temporary PIN for a student or teacher, invalidates active sessions, and flags `must_change_pin = 1`.

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
  * `403 Forbidden`: Teacher attempting to reset an `admin` PIN.
  * `404 Not Found`: Target user ID not found or account is soft-deleted.

---

### <a id="delete-staff-users"></a>`DELETE /api/v1/staff/users/{user_id}`

Soft-deletes an account. Preserves student ID and educational activity logs (`turn_logs`, `quiz_session_votes`) while anonymizing the username, deactivating active sessions, and unlinking assigned hardware clickers.

* **Authorization**: Teacher (targets `student`, `teacher`), Admin (targets any role)
* **Guards**:
  * **Last-Admin Guard**: Cannot delete the final remaining active administrator account (`409 Conflict`).
  * Teachers cannot delete administrators (`403 Forbidden`).
* **Path Parameters**:
  * `user_id` (`integer`, required): Target user ID.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Account deleted."
    }
    ```
  * `403 Forbidden`: Teacher attempting to delete an `admin` account.
  * `404 Not Found`: Target user ID not found or already deleted.
  * `409 Conflict`: Attempting to delete the last remaining admin.

---

### <a id="post-staff-users-recover"></a>`POST /api/v1/staff/users/{user_id}/recover`

Restores a soft-deleted account under a new unique username, sets a temporary PIN, and flags `must_change_pin = 1`.

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
  * `403 Forbidden`: Teacher attempting to recover an `admin` account.
  * `404 Not Found`: Target is not soft-deleted or does not exist.
  * `409 Conflict`: Target recovery username is already taken.

---

### <a id="get-staff-audit-logs"></a>`GET /api/v1/staff/audit-logs`

Reads up to 500 immutable append-only audit trail records. Tracks critical administrative events (`pin_reset`, `account_deleted`, `account_recovered`, `device_assigned`).

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

## Related Specifications

* **[API Gateway & Policies](README.md)**: RBAC permission hierarchy and role matrices.
* **[Authentication & Users](auth.md)**: Session tokens and personal profile management.
* **[Hardware Fleet Management](devices.md)**: ESP32 clicker assignment and registration.
