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

## Installation

Use Python 3.10 or newer and run these commands from this directory. Installing the project with `-e .` reads `pyproject.toml` and installs all runtime dependencies.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

If `python` is not available, use the Python launcher instead:

```powershell
py -3.10 -m venv .venv
```

For Command Prompt, activate the environment with `.venv\Scripts\activate.bat`.

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

### Conda (Windows or Linux)

```bash
conda create -n tutorbox-backend python=3.10
conda activate tutorbox-backend
python -m pip install --upgrade pip
python -m pip install -e .
```

To install development and testing tools as well, use `python -m pip install -e ".[dev]"` after activating the environment.

## Run the API

After activating the virtual or Conda environment:

```bash
python -m uvicorn src.main:app --reload
```

On Linux, `python3 -m uvicorn src.main:app --reload` is equivalent. The API documentation is available at <http://127.0.0.1:8000/docs>.

The application creates `tutorbox.db` in the project root when it starts. Set `DATABASE_PATH` to use a different SQLite database location.

## Run Tests

```bash
python -m pytest
```

On Linux, `python3 -m pytest` is equivalent. The pytest configuration in `pyproject.toml` discovers the `tests/` directory and includes a coverage report for `src/`.

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
