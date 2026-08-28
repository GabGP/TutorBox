# TutorBox Backend

[![ci-backend](https://github.com/GabGP/TutorBox/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/GabGP/TutorBox/actions/workflows/ci-backend.yml)

FastAPI application designed to run on the NVIDIA Jetson Orin Nano, with local development support on Windows and Linux.

> [TutorBox](../README.md) / **Backend** • [Documentation](../docs/README.md) • [API Reference](../docs/api-reference.md) • [Database Schema](../docs/database-schema.md)

---

## Table of Contents
- [1. Components & Architecture](#1-components--architecture)
- [2. API Surface Summary](#2-api-surface-summary)
- [3. Environment Setup](#3-environment-setup)
- [4. Installation & Workflow](#4-installation--workflow)
  - [A. Development Mode](#a-development-mode-local-coding--testing)
  - [B. Production Mode](#b-production-mode)
- [5. Testing & Quality Assurance](#5-testing--quality-assurance)
- [6. Project Structure](#6-project-structure)
- [Next Steps](#next-steps)


---

## 1. Components & Architecture

- **FastAPI REST API**: Health-check and username/PIN login endpoints.
- **Authentication**: Bcrypt-hashed PINs and active sessions.
- **Database**: SQLite with idempotent SQL migrations.

The following items are placeholders for planned work and are not fully implemented in the current backend:

- **WebSocket endpoints**: Real-time interactions and shared chat rooms.
- **Pedagogical Logic**: Socratic hint-escalation ladder state machine.
- **Math Validation**: Deterministic SymPy engine and containment guardrail.
- **ASR Service**: Meta Omnilingual ASR 300M CTC int8 (`sherpa-onnx`) integration for K'iche' speech-to-text.

<<<<<<< Updated upstream
## Environment Setup
=======
---

## 2. API Surface Summary

> [!TIP]
> For complete request/response JSON schemas, error trigger matrices, and Swagger instructions, see the **[REST API Reference](../docs/api-reference.md)**. For the Entity-Relationship model and table dictionaries, see the **[Database Schema Reference](../docs/database-schema.md)**.

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

## 3. Environment Setup
>>>>>>> Stashed changes

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

## 4. Installation & Workflow

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

<<<<<<< Updated upstream
#### Running Tests & Linters:
Run pytest with code coverage
```bash
python -m pytest
```
Run Ruff linter and formatter checks manually
```
ruff check .
ruff format --check .
```

=======
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
## Project Structure
=======
---

## 5. Testing & Quality Assurance

### Running the Test Suite:
Run pytest with code coverage across the entire test suite:
```bash
python -m pytest
```

### Running Scoped Subpackage Tests:
Run isolated test directories during focused development:
```bash
python -m pytest tests/api/staff/ -o addopts="--strict-markers"
python -m pytest tests/security/ -o addopts="--strict-markers"
```

### Code Formatting & Static Analysis:
Run Ruff linter and formatter checks manually:
```bash
ruff check .
ruff format --check .
```

Auto-format all code:
```bash
ruff format .
```

---

## 6. Project Structure
>>>>>>> Stashed changes

Generated environments, caches, and build artifacts are omitted from this overview.

```text
.
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_add_user_role.sql
│   └── 003_add_lookup_indexes.sql
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── health.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── migrations.py
│   └── security/
│       ├── __init__.py
│       ├── auth.py
│       └── rate_limit.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_database.py
│   ├── test_health.py
│   ├── test_migrations.py
│   ├── test_rate_limit.py
│   └── test_security_pin.py
├── pyproject.toml
└── README.md
```

---

## Next Steps

* **[REST API Reference & Contracts](../docs/api-reference.md)**: Explore the endpoint contracts, request/response schemas, and RBAC matrix.
* **[Database Schema Reference](../docs/database-schema.md)**: Explore the SQLite table definitions and ER diagram.
* **[Documentation Portal](../docs/README.md)**: View the overarching documentation index.
* **[Root Repository Overview](../README.md)**: Return to the project root overview.
