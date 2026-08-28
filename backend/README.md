# TutorBox Backend

[![ci-backend](https://github.com/GabGP/TutorBox/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/GabGP/TutorBox/actions/workflows/ci-backend.yml)

FastAPI application designed to run on the NVIDIA Jetson Orin Nano, with local development support on Windows and Linux.

## Components

- **FastAPI REST API**:
  - Health checks (`/health`)
  - Authentication (`/login`, `/logout`)
  - Student self-service lifecycle (`/signup`, `/users/me`, `/users/me/pin`, `/users/me/username`)
  - Staff management (`/users`, `/users/{id}/reset-pin`, `/users/{id}`, `/users/{id}/recover`)
  - Privileged system audit trail (`/audit-logs`)
- **Security & Access Control**:
  - Role-based access control (RBAC) with `student`, `teacher`, and `admin` roles.
  - Forced PIN rotation enforcement and policy validation (4–8 numeric digits).
  - In-memory rate limiting: credential lockout limiter (consecutive failure backoff) and global sliding window limiters (signup / rate-throttling).
  - Bearer session token lifecycle with active session deactivation.
  - Zero-credential logging guards and anti-oracle check ordering.
- **Database & Migrations**:
  - SQLite database with foreign keys and index optimization.
  - Numbered, idempotent schema migrations (`001` through `006`).
  - Append-only `audit_logs` table tracking privileged user and account mutations.

The following items are placeholders for planned work and are not fully implemented in the current backend:

- **WebSocket endpoints**: Real-time interactions and shared chat rooms.
- **Pedagogical Logic**: Socratic hint-escalation ladder state machine.
- **Math Validation**: Deterministic SymPy engine and containment guardrail.
- **ASR Service**: Meta Omnilingual ASR 300M CTC int8 (`sherpa-onnx`) integration for K'iche' speech-to-text.

---

## API Summary

| Method | Path | Auth / Role | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | System and SQLite health check |
| `POST` | `/signup` | Public (Rate-limited) | Student self-registration |
| `POST` | `/login` | Public (Rate-limited) | Authenticate with username and PIN; returns session token |
| `POST` | `/logout` | Bearer Token | Invalidate current caller session |
| `GET` | `/users/me` | Bearer Token | Return profile of authenticated user |
| `PATCH` | `/users/me/pin` | Bearer Token | Self-service PIN change (clears forced rotation flag) |
| `PATCH` | `/users/me/username` | Bearer Token | Self-service username change |
| `GET` | `/users` | Teacher, Admin | List active accounts, or deleted accounts with `?include_deleted=true` |
| `POST` | `/users` | Teacher, Admin | Staff user creation (Teachers: student/teacher; Admins: any role) |
| `POST` | `/users/{id}/reset-pin` | Teacher, Admin | Issue 6-digit temp PIN, invalidate sessions, and require PIN rotation |
| `DELETE` | `/users/{id}` | Teacher, Admin | Soft-delete user, anonymize username, preserve telemetry, last-admin guard |
| `POST` | `/users/{id}/recover` | Teacher, Admin | Restore soft-deleted account under new username with temporary PIN |
| `GET` | `/audit-logs` | Admin Only | View up to 500 append-only audit trail records |

---

## Environment Setup

Ensure you are using Python 3.10 or newer.

### Create and Activate Virtual Environment

#### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```
*(If `python` is not available, use `py -3.10 -m venv .venv`)*

#### Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

#### Conda (Windows or Linux)
```bash
conda create -n tutorbox-backend python=3.10
conda activate tutorbox-backend
python -m pip install --upgrade pip
```

---

## Installation & Workflow

Choose the installation mode matching your target environment:

### A. Development Mode (Local Coding & Testing)

Installs the package in **editable mode** (`-e`) along with development dependencies (`pytest`, `pytest-cov`, `ruff`, `pre-commit`):

```bash
python -m pip install -e ".[dev]"
```

> [!IMPORTANT]
> **Developer Reminder: Install Pre-Commit Hooks**
> All developers contributing code must install the Git pre-commit hooks to enforce automatic formatting, linting (Ruff), and syntax validation before every commit:
> ```bash
> pre-commit install
> ```

#### Running in Development:
Run Uvicorn with `--reload` to automatically refresh the server whenever you edit source code:
```bash
python -m uvicorn src.main:app --reload
```
The interactive API documentation is available at <http://127.0.0.1:8000/docs>.

#### Running Tests & Linters:
Run pytest with full code coverage:
```bash
python -m pytest
```

Run a specific test subpackage:
```bash
python -m pytest tests/api/staff/ -o addopts="--strict-markers"
```

Run Ruff linter and formatter checks manually:
```bash
ruff check .
ruff format --check .
```

---

### B. Production Mode

Installs a **static production package** with minimal runtime dependencies (excluding dev tools and test suites):

```bash
python -m pip install .
```

#### Running in Production:
Run Uvicorn bound to all network interfaces (`0.0.0.0`) without `--reload`:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The database `tutorbox.db` will be initialized and migrated automatically on startup. Use the `DATABASE_PATH` environment variable to configure a custom SQLite file location.

---

## Project Structure

Generated environments, caches, and build artifacts are omitted from this overview.

```text
backend/
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_add_user_role.sql
│   ├── 003_add_lookup_indexes.sql
│   ├── 004_add_must_change_pin.sql
│   ├── 005_add_users_deleted_at.sql
│   └── 006_add_audit_logs.sql
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── login.py
│   │   │   └── logout.py
│   │   ├── health.py
│   │   ├── staff/
│   │   │   ├── __init__.py
│   │   │   ├── audit.py
│   │   │   ├── lifecycle.py
│   │   │   ├── reset_pin.py
│   │   │   └── users.py
│   │   └── users/
│   │       ├── __init__.py
│   │       ├── credentials.py
│   │       ├── profile.py
│   │       └── signup.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── audit.py
│   │   ├── database.py
│   │   └── migrations.py
│   └── security/
│       ├── __init__.py
│       ├── auth.py
│       ├── rate_limit/
│       │   ├── __init__.py
│       │   ├── lockout.py
│       │   └── sliding_window.py
│       ├── session.py
│       └── validation.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── test_login.py
│   │   │   └── test_logout.py
│   │   ├── staff/
│   │   │   ├── __init__.py
│   │   │   ├── test_audit.py
│   │   │   ├── test_delete.py
│   │   │   ├── test_recover.py
│   │   │   ├── test_reset_pin.py
│   │   │   └── test_users.py
│   │   ├── users/
│   │   │   ├── __init__.py
│   │   │   ├── test_change_pin.py
│   │   │   ├── test_change_username.py
│   │   │   ├── test_profile.py
│   │   │   └── test_signup.py
│   │   └── test_health.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── test_audit.py
│   │   ├── test_database.py
│   │   └── test_migrations.py
│   └── security/
│       ├── __init__.py
│       ├── test_auth_pin.py
│       ├── test_rate_limit.py
│       ├── test_security_pin.py
│       └── test_session_auth.py
├── pyproject.toml
└── README.md
```
