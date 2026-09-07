# Core Identity, Authentication & Fleet Schema

Technical specification for student and staff credentials, bearer sessions, ESP32 hardware clicker inventory, and security audit logs in **TutorBox**.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Database](README.md) › **Core Schema** • **Related:** [Quiz Schema](quiz.md) • [Dialogue Telemetry](dialogue.md) • [Migrations](migrations.md)

</div>

---

## Table of Contents
- [1. Data Dictionary](#1-data-dictionary)
  - [Table: `users`](#table-users)
  - [Table: `sessions`](#table-sessions)
  - [Table: `devices`](#table-devices)
  - [Table: `audit_logs`](#table-audit_logs)
- [2. Identity & Fleet Lifecycle Policies](#2-identity--fleet-lifecycle-policies)
  - [A. Soft-Deletion & Username Freeing](#a-soft-deletion--username-freeing)
  - [B. Last-Admin Guard](#b-last-admin-guard)
  - [C. Device Unlinking on Deletion](#c-device-unlinking-on-deletion)
- [Related Specifications](#related-specifications)

---

## <a id="1-data-dictionary"></a>1. Data Dictionary

### Table: `users`
Stores student and staff credentials, roles, and lifecycle states.

| Column | Type | Constraints | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | — | Unique internal user identifier. |
| `username` | `TEXT` | `UNIQUE NOT NULL` | — | User login handle (3–32 chars, `[A-Za-z0-9_.-]`). Anonymized to `deleted_user_{id}_{hex}` upon soft-deletion. |
| `hashed_pin` | `TEXT` | `NOT NULL` | — | Bcrypt hash (`$2b$`) of the 4–8 digit PIN. Plaintext PINs are never stored. |
| `role` | `TEXT` | `NOT NULL`, `CHECK(role IN ('student', 'teacher', 'admin'))` | `'student'` | Access role determining authorization boundaries. |
| `created_at` | `TIMESTAMP` | — | `CURRENT_TIMESTAMP` | UTC timestamp of account creation. |
| `must_change_pin`| `INTEGER` | `NOT NULL`, `CHECK(must_change_pin IN (0, 1))` | `0` | Flag forcing PIN change on next login (`1` = change required). |
| `deleted_at` | `TIMESTAMP` | `NULL` | `NULL` | Timestamp of account soft-deletion (`NULL` for active accounts). |
| `former_username`| `TEXT` | `NULL` | `NULL` | The username held prior to soft-deletion (for recovery / roster display). |

---

### Table: `sessions`
Tracks active and revoked bearer sessions.

| Column | Type | Constraints | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `TEXT` | `PRIMARY KEY` | — | UUIDv4 string issued to client as Bearer token. |
| `user_id` | `INTEGER` | `NOT NULL`, `FOREIGN KEY -> users(id) ON DELETE CASCADE` | — | Foreign key referencing account owner. |
| `created_at` | `TIMESTAMP` | — | `CURRENT_TIMESTAMP` | UTC timestamp of session creation. |
| `is_active` | `INTEGER` | `CHECK(is_active IN (0, 1))` | `1` | `1` if session is active; `0` if revoked by logout, PIN change, reset, or deletion. |

---

### Table: `devices`
Registry of physical ESP32 clickers and active 1:1 classroom pairings to student accounts.

| Column | Type | Constraints | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `device_id` | `TEXT` | `PRIMARY KEY` | — | Unique hardware clicker identifier (1–32 chars, e.g. `'1'`, `'ESP32_01'`). |
| `assigned_user_id` | `INTEGER` | `UNIQUE`, `FOREIGN KEY -> users(id) ON DELETE SET NULL` | `NULL` | Currently linked student account ID (`NULL` when unassigned). |
| `created_at` | `TIMESTAMP` | — | `CURRENT_TIMESTAMP` | UTC timestamp when clicker was registered into the fleet. |

---

### Table: `audit_logs`
Append-only audit trail recording sensitive operational, staff, and hardware pairing actions.

| Column | Type | Constraints | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | — | Sequential audit log record ID. |
| `actor_user_id` | `INTEGER` | `NULL` | `NULL` | User ID of the caller who initiated the action (`NULL` for public self-signup). |
| `action` | `TEXT` | `NOT NULL` | — | Action identifier string (validated against `VALID_ACTIONS`). |
| `target_user_id` | `INTEGER` | `NULL` | `NULL` | User ID of the affected account. |
| `created_at` | `TIMESTAMP` | — | `CURRENT_TIMESTAMP` | UTC timestamp when event was recorded. |

#### Valid Audit Action Strings
* `signup`: Student self-registration.
* `user_created`: Account created by staff.
* `pin_reset`: Temporary PIN issued by staff.
* `username_changed`: Username changed by user.
* `pin_changed`: PIN rotated by user.
* `account_deleted`: Account soft-deleted.
* `account_recovered`: Soft-deleted account restored.
* `device_registered`: Hardware clicker registered into appliance fleet.
* `device_assigned`: Clicker linked to student.
* `device_unassigned`: Clicker unlinked from student.
* `device_deleted`: Clicker removed from fleet.

---

## <a id="2-identity--fleet-lifecycle-policies"></a>2. Identity & Fleet Lifecycle Policies

### <a id="a-soft-deletion--username-freeing"></a>A. Soft-Deletion & Username Freeing
When an account soft-deletion is executed:
1. `deleted_at` is set to `CURRENT_TIMESTAMP`.
2. `former_username` preserves the user's original username for roster display.
3. `username` is renamed to an anonymized placeholder (`deleted_user_{id}_{hex}`) to **immediately free** the original username for new registrations.
4. `hashed_pin` is replaced with an unmatchable bcrypt hash (`hash_pin(secrets.token_hex(16))`).
5. All active sessions in `sessions` are deactivated (`is_active = 0`).
6. **Telemetry Preservation**: Rows in `turn_logs` and `quiz_session_votes` remain intact and joinable to `users` via `user_id`.

### <a id="b-last-admin-guard"></a>B. Last-Admin Guard
The application enforces that the appliance must never lose its final administrator. Deleting the last active user with `role = 'admin'` is rejected with `409 Conflict`.

### <a id="c-device-unlinking-on-deletion"></a>C. Device Unlinking on Deletion
When an account is deleted or soft-deleted, any associated hardware clicker has `assigned_user_id` set to `NULL`, automatically freeing the device for reassignment to another student.

---

## Related Specifications

* **[Database Hub & ER Model](README.md)**: Architecture overview, full Mermaid ER diagram, and index definitions.
* **[Auth & Users API Spec](../api/auth.md)**: API routes interacting with `users` and `sessions`.
* **[Devices API Spec](../api/devices.md)**: Hardware clicker assignment endpoints.
* **[Staff Admin API Spec](../api/staff.md)**: User management and audit log endpoints.
