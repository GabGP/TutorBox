# TutorBox Backend

[![ci-backend](https://github.com/GabGP/TutorBox/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/GabGP/TutorBox/actions/workflows/ci-backend.yml)

FastAPI application designed to run on the NVIDIA Jetson Orin Nano, with local development support on Windows and Linux.

<div align="center">

| 🏠 [TutorBox](../README.md) | 📚 [Docs](../docs/README.md) | ⚙️ **Backend** | 📱 [PWA](../pwa/README.md) | 🔌 [Infra](../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Backend** › **Overview** • **Related:** [REST API Reference](../docs/api-reference.md) • [Database Schema](../docs/database-schema.md) • [Hardware Topology](../docs/architecture/hardware-topology.md)

</div>

---

## Table of Contents
- [1. Components & Architecture](#1-components--architecture)
- [2. API Contracts & Specifications](#2-api-contracts--specifications)
- [3. Environment Setup](#3-environment-setup)
  - [Create and Activate Virtual Environment](#create-and-activate-virtual-environment)
  - [Environment Variables & Configuration (`.env`)](#environment-variables--configuration-env)
- [4. Installation & Workflow](#4-installation--workflow)
  - [A. Development Mode (Local Coding & Testing)](#a-development-mode-local-coding--testing)
  - [B. Production Mode](#b-production-mode)
- [5. Testing & Quality Assurance](#5-testing--quality-assurance)
  - [Running the Test Suite](#running-the-test-suite)
  - [Running Parallel Tests (`pytest-xdist`)](#running-parallel-tests-pytest-xdist)
  - [Running Scoped Subpackage Tests](#running-scoped-subpackage-tests)
  - [Code Formatting & Static Analysis](#code-formatting--static-analysis)
- [6. Project Structure](#6-project-structure)
- [Next Steps](#next-steps)

---

## <a id="1-components--architecture"></a>1. Components & Architecture

- **FastAPI Core Application**:
  - Modular sub-routers for health probes, authentication sessions, student self-service, staff administration, and physical ESP32 clicker fleet management.
  - OpenAPI automated documentation generator (`/docs` and `/openapi.json`).
- **Security & Access Control**:
  - Role-based access control (RBAC) with `student`, `teacher`, and `admin` roles.
  - Forced PIN rotation enforcement and policy validation (4–8 numeric digits).
  - In-memory rate limiting: credential lockout limiter (consecutive failure backoff) and global sliding window limiters (signup / rate-throttling).
  - Bearer session token lifecycle with active session deactivation.
  - Zero-credential logging guards and anti-oracle check ordering.
- **Platform Infrastructure (`core/`)**:
  - **Centralized Configuration & Environment Loader (`core/config`)**: Typed domain dataclasses (`DatabaseConfig`, `SecurityConfig`, `LLMConfig`, `QuizConfig`), safe `.env` file discovery, early bootstrapping, and range/type coercion with fallback to safe defaults.
  - **Database & Migrations (`core/db`)**: SQLite with foreign keys, index optimization, and WAL mode; numbered idempotent migrations; append-only audit logging; repository layers for quiz questions, sessions, rounds, votes, and generation telemetry.
  - **Security & Access Control (`core/security`)**: Role-based access control (RBAC), forced PIN rotation, in-memory rate limiting (credential lockout & sliding window), bearer session token lifecycle, and zero-credential logging guards.
  - **Mathematical Engine & SymPy Parser (`core/math_engine`)**: Deterministic SymPy AST parsing, arithmetic evaluation, and linear equation solver with non-equality proofs.
  - **LLM Client Layer (`core/llm`)**: Abstract client protocol, local HTTP SLM client with timeout/retry safeguards, and mock client for deterministic testing.

- **Appliance Operating Modes (`modes/`)**:
  - **Mode 1: Classroom Quiz Mode (`modes/quiz/`)**: Versioned JSON Schema contracts, diagnostic distractors with 32 misconception slugs, 66-question seed bank, multi-stage prompt rejection pipeline with anti-guessing shuffler, and real-time session engine (`modes/quiz/session/`) featuring monotonic countdown timer, first-press locks (`UNIQUE(round_id, student_id)`), and deterministic >51% Rule evaluator.
  - **Mode 2: Socratic Tutor Mode (`modes/socratic/`)**: Planned for Week 5 (mobile conversational math practice, Socratic hint ladders, SymPy containment).
  - **Mode 3: Offline Primary Games Mode (`modes/games/`)**: Planned for Week 6 (offline educational games, student error event ingestion, opportunistic AP sync).

The following items are planned deliverables across upcoming milestone phases:

- **Offline Voice Feedback (Week 4)**: Jetson offline neural TTS (Piper-TTS / Sherpa-ONNX) in Spanish and K'iche' for distractor remediation.
- **Socratic Tutor Engine (Week 5)**: Socratic hint-escalation state machine and SymPy math containment guardrail.
- **Offline Games Ingestion (Week 6)**: Normalization and ingestion of offline game error events with opportunistic synchronization.
- **ESP32 Hardware Clickers (Week 7)**: Physical firmware, button debounce, RGB LED feedback, and `VoteTransport` driver integration.
- **Unified Analytics (Week 8)**: Transversal student error synthesis across all 3 modes and printable offline weekly reports.

---

## <a id="2-api-contracts--specifications"></a>2. API Contracts & Specifications

For further details check these documents:

* **[REST API Reference & Contracts (`docs/api-reference.md`)](../docs/api-reference.md)**: Authoritative specification for all REST endpoints, complete request/response JSON schemas, Role-Based Access Control (RBAC) matrix, error status triggers, and anti-oracle validation rules.
* **[Database Schema & ER Model (`docs/database-schema.md`)](../docs/database-schema.md)**: Authoritative specification for SQLite tables, columns, constraints, performance indexes, data lifecycle policies, and migration logs.
* **Interactive OpenAPI Swagger UI**: When running the backend server locally, navigate to <http://127.0.0.1:8000/docs> for live interactive testing or <http://127.0.0.1:8000/openapi.json> for the machine-readable schema.

---

## <a id="3-environment-setup"></a>3. Environment Setup

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

### Environment Variables & Configuration (`.env`)

Copy the template `.env.example` to `.env` in the repository root to customize database paths, bcrypt work factors, rate limits, and SLM inference parameters:


---

## <a id="4-installation--workflow"></a>4. Installation & Workflow

Choose the installation mode matching your target environment:

### <a id="a-development-mode-local-coding--testing"></a>A. Development Mode (Local Coding & Testing)

Installs the package in **editable mode** (`-e`) along with development dependencies (`pytest`, `pytest-cov`, `pytest-env`, `pytest-xdist`, `ruff`, `pre-commit`):

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

---

### <a id="b-production-mode"></a>B. Production Mode

Installs a **static production package** with minimal runtime dependencies (excluding dev tools and test suites):

```bash
python -m pip install .
```

#### Running in Production:
Run Uvicorn bound to all network interfaces (`0.0.0.0`) without `--reload`:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The database `tutorbox.db` will be initialized inside `.cache/db/` and migrated automatically on startup. Use the `DATABASE_PATH` environment variable to configure a custom SQLite file location.

---

## <a id="5-testing--quality-assurance"></a>5. Testing & Quality Assurance

### Running the Test Suite:
Run pytest with code coverage across the entire test suite:
```bash
python -m pytest
```

### Running Parallel Tests (`pytest-xdist`):
Distribute test execution across multiple CPU workers (useful as test volume scales):
```bash
python -m pytest -n auto
# Or specify worker count:
python -m pytest -n 4
```

### Running Scoped Subpackage Tests:
Run isolated test directories during focused development:
```bash
python -m pytest tests/api/staff/ -o addopts="--strict-markers"
python -m pytest tests/core/security/ -o addopts="--strict-markers"
python -m pytest tests/modes/quiz/ -o addopts="--strict-markers"
```

### <a id="code-formatting--static-analysis"></a>Code Formatting & Static Analysis:
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

## <a id="6-project-structure"></a>6. Project Structure

Generated environments, caches, and build artifacts are omitted from this overview.

```text
backend/
├── migrations/        # Idempotent SQLite schema migration scripts
├── schemas/           # Canonical versioned JSON Schema contract artifacts (Draft 2020-12)
│   └── v1/            # Version 1.0.0 schema artifacts (quiz_question.schema.json)
├── src/
│   ├── api/           # FastAPI route modules (auth, health, quiz, session, staff, users) mounted under /api/v1
│   ├── core/          # Platform infrastructure & transversal foundation
│   │   ├── config/    # Centralized typed domain settings engine and .env environment loader
│   │   ├── db/        # SQLite connection, repositories (quiz, session, round, vote, telemetry), migrations & audit
│   │   ├── llm/       # Abstract LLM client interface, HTTP local SLM client, and test mock client
│   │   ├── math_engine/ # Deterministic SymPy AST parsing, arithmetic, and linear equation solver
│   │   └── security/  # bcrypt PIN hashing, session tokens, and rate limiters
│   └── modes/         # TutorBox bounded appliance operating modes
│       ├── quiz/      # Mode 1: Classroom Quiz Mode (contracts, generator, seed data, validator)
│       │   └── session/ # Real-time session engine, >51% rule evaluator, countdown timer, vote processor
│       ├── socratic/  # Mode 2: Socratic Math Practice Tutor (Week 5 stub)
│       └── games/     # Mode 3: Offline Primary Educational Games (Week 6 stub)
├── tests/             # Pytest test suite mirroring src/ (core/, modes/, api/) with 100% coverage
├── pyproject.toml     # Project dependencies, tool configurations (ruff, pytest, coverage)
└── README.md          # Backend developer documentation and local setup guide
```

---

## Next Steps

* **[REST API Reference & Contracts](../docs/api-reference.md)**: Explore the endpoint contracts, request/response schemas, and RBAC matrix.
* **[Database Schema Reference](../docs/database-schema.md)**: Explore the SQLite table definitions and ER diagram.
* **[Documentation Portal](../docs/README.md)**: View the overarching documentation index.
* **[Root Repository Overview](../README.md)**: Return to the project root overview.
