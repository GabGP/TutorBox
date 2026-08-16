# TutorBox Backend

FastAPI application designed to run on the NVIDIA Jetson Orin Nano, with local development support on Windows and Linux.

## Components

- **FastAPI REST API**: Health-check and username/PIN login endpoints.
- **Authentication**: Bcrypt-hashed PINs and active sessions.
- **Database**: SQLite with idempotent SQL migrations.

The following items are placeholders for planned work and are not fully implemented in the current backend:

- **WebSocket endpoints**: Real-time interactions and shared chat rooms.
- **Pedagogical Logic**: Socratic hint-escalation ladder state machine.
- **Math Validation**: Deterministic SymPy engine and containment guardrail.
- **ASR Service**: Meta Omnilingual ASR 300M CTC int8 (`sherpa-onnx`) integration for K'iche' speech-to-text.

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
```bash
# Run pytest with code coverage
python -m pytest

# Run Ruff linter and formatter checks manually
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
Run Uvicorn bound to all network interfaces (`0.0.0.0`) without `--reload`, using worker processes for concurrency:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2
```

The database `tutorbox.db` will be initialized and migrated automatically on startup. Use the `DATABASE_PATH` environment variable to configure a custom SQLite file location.

## Project Structure

Generated environments, caches, and build artifacts are omitted from this overview.

```text
.
├── migrations/
│   └── 001_initial_schema.sql
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
│       └── auth.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_database.py
│   ├── test_health.py
│   ├── test_migrations.py
│   └── test_security_pin.py
├── pyproject.toml
└── README.md
```
