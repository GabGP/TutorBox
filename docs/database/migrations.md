# SQLite Database Migrations Playbook & Changelog

Comprehensive migration specifications, historical changelog, and execution procedures for **TutorBox**.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [Database](README.md) › **Migrations Playbook** • **Related:** [Database Hub](README.md) • [Backend Guide](../../backend/README.md)

</div>

---

## Table of Contents
- [1. Migration Architecture & Pragmas](#1-migration-architecture--pragmas)
- [2. Migration Changelog Overview](#2-migration-changelog-overview)
- [3. Detailed Migration Specifications](#3-detailed-migration-specifications)
  - [001: Initial Baseline Schema](#001-initial-baseline-schema)
  - [002: Role Check Constraints](#002-role-check-constraints)
  - [003: Foreign Key Lookup Indexes](#003-foreign-key-lookup-indexes)
  - [004: Forced PIN Rotation Flag](#004-forced-pin-rotation-flag)
  - [005: Soft-Deletion & Username Freeing](#005-soft-deletion--username-freeing)
  - [006: Append-Only Security Audit Logging](#006-append-only-security-audit-logging)
  - [007: ESP32 Hardware Fleet Inventory](#007-esp32-hardware-fleet-inventory)
  - [008: Diagnostic Question Bank](#008-diagnostic-question-bank)
  - [009: SLM Telemetry & Rejection History](#009-slm-telemetry--rejection-history)
  - [010: Quiz Sessions, Rounds & First-Press Voting](#010-quiz-sessions-rounds--first-press-voting)
- [4. Migration Workflow & Verification Runbook](#4-migration-workflow--verification-runbook)
- [5. Rollback & Disaster Recovery](#5-rollback--disaster-recovery)

---

## <a id="1-migration-architecture--pragmas"></a>1. Migration Architecture & Pragmas

TutorBox utilizes sequential idempotent SQL migration files executed automatically at application startup by `backend/src/db/migrations.py`.

* **Storage Location**: `backend/migrations/<NNN>_<description>.sql`
* **Version Registry**: Every applied migration is tracked in the `schema_migrations` table with its integer version and timestamp.
* **Idempotency Rule**: All migration files must be safe to execute multiple times (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`).
* **Runtime Pragmas**:
  ```sql
  PRAGMA foreign_keys = ON;
  PRAGMA journal_mode = WAL;
  PRAGMA busy_timeout = 5000;
  ```

---

## <a id="2-migration-changelog-overview"></a>2. Migration Changelog Overview

| Version | Migration File | Target Subsystem | Key Tables & Changes | Milestone |
| :---: | :--- | :--- | :--- | :---: |
| **001** | `001_initial_schema.sql` | Core Storage | `schema_migrations`, `users`, `sessions`, `turn_logs` | Week 1 |
| **002** | `002_add_user_role.sql` | Security / RBAC | Adds `role` column (`student`, `teacher`, `admin`) to `users` | Week 1 |
| **003** | `003_add_lookup_indexes.sql` | Performance | Adds `idx_sessions_user_id`, `idx_turn_logs_session_id` | Week 1 |
| **004** | `004_add_must_change_pin.sql` | Security / PIN | Adds `must_change_pin` column to `users` | Week 1 |
| **005** | `005_add_users_deleted_at.sql` | User Lifecycle | Adds `deleted_at`, `former_username` for soft-deletion | Week 1 |
| **006** | `006_add_audit_logs.sql` | Security Audit | Creates `audit_logs` table and lookup indexes | Week 1 |
| **007** | `007_add_devices.sql` | Hardware Fleet | Creates `devices` table and `idx_devices_assigned_user` | Week 1 |
| **008** | `008_add_quiz_questions.sql` | Question Bank | Creates `quiz_questions` table with JSON distractors | Week 2 |
| **009** | `009_add_quiz_generation_logs.sql` | AI Telemetry | Creates `quiz_generation_logs` for latency and retry metrics | Week 2 |
| **010** | `010_add_quiz_sessions_and_votes.sql` | Session Engine | Creates `quiz_sessions`, `quiz_session_rounds`, `quiz_session_votes` | Week 3 |

---

## <a id="3-detailed-migration-specifications"></a>3. Detailed Migration Specifications

### <a id="001-initial-baseline-schema"></a>001: Initial Baseline Schema
* **File**: [`backend/migrations/001_initial_schema.sql`](../../backend/migrations/001_initial_schema.sql)
* **Description**: Sets up tracking table `schema_migrations` and core entities: `users` (with bcrypt hash), `sessions` (UUIDv4 tokens), and `turn_logs` (student prompt and SymPy AST storage).

### <a id="002-role-check-constraints"></a>002: Role Check Constraints
* **File**: [`backend/migrations/002_add_user_role.sql`](../../backend/migrations/002_add_user_role.sql)
* **Description**: Introduces the `role` column to `users` with check constraint `role IN ('student', 'teacher', 'admin')` defaulting to `'student'`.

### <a id="003-foreign-key-lookup-indexes"></a>003: Foreign Key Lookup Indexes
* **File**: [`backend/migrations/003_add_lookup_indexes.sql`](../../backend/migrations/003_add_lookup_indexes.sql)
* **Description**: Creates B-tree indexes on foreign keys to eliminate full table scans during session lookups and dialogue history retrieval:
  * `idx_sessions_user_id ON sessions(user_id)`
  * `idx_turn_logs_session_id ON turn_logs(session_id)`

### <a id="004-forced-pin-rotation-flag"></a>004: Forced PIN Rotation Flag
* **File**: [`backend/migrations/004_add_must_change_pin.sql`](../../backend/migrations/004_add_must_change_pin.sql)
* **Description**: Adds boolean column `must_change_pin INTEGER NOT NULL DEFAULT 0` to support teacher-initiated credential resets.

### <a id="005-soft-deletion--username-freeing"></a>005: Soft-Deletion & Username Freeing
* **File**: [`backend/migrations/005_add_users_deleted_at.sql`](../../backend/migrations/005_add_users_deleted_at.sql)
* **Description**: Adds `deleted_at TIMESTAMP` and `former_username TEXT` columns. Enables soft deletion so deleted student data retains pedagogical audit trails while releasing the username string.

### <a id="006-append-only-security-audit-logging"></a>006: Append-Only Security Audit Logging
* **File**: [`backend/migrations/006_add_audit_logs.sql`](../../backend/migrations/006_add_audit_logs.sql)
* **Description**: Creates `audit_logs` table recording actor, target, and security actions (`pin_reset`, `account_deleted`, `account_recovered`). Includes indexes `idx_audit_logs_actor` and `idx_audit_logs_target`.

### <a id="007-esp32-hardware-fleet-inventory"></a>007: ESP32 Hardware Fleet Inventory
* **File**: [`backend/migrations/007_add_devices.sql`](../../backend/migrations/007_add_devices.sql)
* **Description**: Creates `devices` table mapping hardware clicker IDs (`device_id PK`) to optional student IDs (`assigned_user_id UK REFERENCES users(id) ON DELETE SET NULL`). Includes `idx_devices_assigned_user`.

### <a id="008-diagnostic-question-bank"></a>008: Diagnostic Question Bank
* **File**: [`backend/migrations/008_add_quiz_questions.sql`](../../backend/migrations/008_add_quiz_questions.sql)
* **Description**: Creates `quiz_questions` table storing question text, options JSON, correct answer, diagnostic distractors JSON (misconception slug + Spanish explanation), and SymPy verification status. Includes composite indexes `idx_quiz_questions_topic` and `idx_quiz_questions_created`.

### <a id="009-slm-telemetry--rejection-history"></a>009: SLM Telemetry & Rejection History
* **File**: [`backend/migrations/009_add_quiz_generation_logs.sql`](../../backend/migrations/009_add_quiz_generation_logs.sql)
* **Description**: Creates `quiz_generation_logs` table recording SLM latency in milliseconds, attempt counts, success status, and JSON rejection histories. Includes indexes on `user_id`, `topic`, and `created_at`.

### <a id="010-quiz-sessions-rounds--first-press-voting"></a>010: Quiz Sessions, Rounds & First-Press Voting
* **File**: [`backend/migrations/010_add_quiz_sessions_and_votes.sql`](../../backend/migrations/010_add_quiz_sessions_and_votes.sql)
* **Description**: Creates the real-time quiz session persistence layer:
  * `quiz_sessions`: match metadata, topic, status (`lobby`, `active`, `completed`), duration.
  * `quiz_session_rounds`: individual question rounds, ordered round indexes, round status (`pending`, `open`, `closed`, `revealed`).
  * `quiz_session_votes`: individual student vote records with **strict database-level first-press lock enforcement** via:
    ```sql
    UNIQUE(round_id, student_id)
    ```
  * Includes performance indexes: `idx_quiz_rounds_session_index`, `idx_quiz_votes_round_student`, `idx_quiz_votes_student`, `idx_quiz_votes_analytics`.

---

## <a id="4-migration-workflow--verification-runbook"></a>4. Migration Workflow & Verification Runbook

Follow these sequential steps when adding or modifying database schemas:

1. **Allocate Version Number**:
   Inspect `backend/migrations/` and pick the next 3-digit integer (e.g. `011_add_tts_cache.sql`).
2. **Author SQL Script**:
   * Write plain SQL using strict SQLite syntax.
   * Use `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`.
   * Never execute destructive schema migrations without migration rollback scripts.
3. **Validate Idempotency & Clean Bootstrap**:
   Run the migration unit test suite:
   ```bash
   pytest backend/tests/db/test_migrations.py
   ```
4. **Update Documentation**:
   * Add the new migration entry to the changelog in this file ([`docs/database/migrations.md`](migrations.md)).
   * Update the ER diagram and Data Dictionary in [`docs/database/README.md`](README.md).
5. **Execute Quality Gate**:
   ```bash
   pre-commit run --all-files
   pytest backend/tests/
   ```

---

## <a id="5-rollback--disaster-recovery"></a>5. Rollback & Disaster Recovery

* **Edge Appliance Backup**: Before applying experimental migrations on physical hardware (Jetson Orin Nano), execute a WAL checkpoint and database backup:
  ```bash
  sqlite3 tutorbox.db "PRAGMA wal_checkpoint(TRUNCATE);"
  cp tutorbox.db tutorbox.db.bak
  ```
* **Migration Table Reversion**: If a migration fails during application bootstrap, SQLite transactions roll back automatically. To manually revert a version entry during development:
  ```sql
  DELETE FROM schema_migrations WHERE version = 10;
  ```

---

## Related Documentation

* **[Database Schema & ER Model](README.md)**: Full table data dictionary, column types, and foreign key relations.
* **[REST API Specifications](../api/README.md)**: Endpoints interacting with persisted database tables.
* **[Week 3 Milestone Summary](../milestones/week-3-session-engine.md)**: Session engine and vote persistence verification.
