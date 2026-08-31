# TutorBox: Autonomous Offline Edge AI Socratic Educational Platform

[![ci-backend](https://github.com/GabGP/TutorBox/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/GabGP/TutorBox/actions/workflows/ci-backend.yml)

<div align="center">

| 🏠 **TutorBox** | 📚 [Docs](docs/README.md) | ⚙️ [Backend](backend/README.md) | 📱 [PWA](pwa/README.md) | 🔌 [Infra](infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Root** › **Overview** • **Quick Links:** [Architecture](docs/README.md#2-system-architecture--modes) • [Roadmap](docs/milestones/roadmap.md) • [API Reference](docs/api-reference.md) • [Database Schema](docs/database-schema.md)

</div>

---

**TutorBox** is an offline Edge AI educational appliance designed for basic education students in rural and off-grid communities with zero internet connectivity. The appliance delivers interactive classroom quizzes, Socratic math tutoring, and offline educational games with dual-language voice output in Spanish and **K'iche'** (`quc_Latn`).

> [!NOTE]
> **Work in Progress**: This project is under active development as an engineering capstone project. Architecture, schemas, and features are subject to ongoing iteration.

---

## Table of Contents
- [1. Project Architecture](#1-project-architecture)
- [2. Hardware Topology](#2-hardware-topology)
- [3. Software & AI Stack](#3-software--ai-stack)
- [4. System Constraints & Guardrails](#4-system-constraints--guardrails)
- [5. Repository Structure](#5-repository-structure)
- [6. Technical Documentation](#6-technical-documentation)
- [Next Steps](#next-steps)

---

## <a id="1-project-architecture"></a>1. Project Architecture

TutorBox operates on a local network topology consisting of an isolated Access Point and an integrated Edge AI Core Appliance.

```mermaid
graph TD
    subgraph AP ["Local Access Point"]
        Router["GL.iNet GL-AR300M16 Router<br/>(SSID: TutorBox - Isolated Local AP)"]
    end

    subgraph Clients ["Client Layer"]
        Students["Student Devices<br/>(Tablets, Smartphones & ESP32 Clickers)"]
    end

    subgraph Core ["Core AI Appliance (NVIDIA Jetson Orin Nano - 8GB Unified RAM)"]
        Nginx["Nginx Web Server & Reverse Proxy"]
        PWA["Compiled React/Vite PWA Static Files"]
        FastAPI["FastAPI Backend Application (:8000)"]
        SymPy["SymPy Math Engine & Containment Guardrail"]
        Pedagogy["Socratic State Machine & Session Engine"]
        SQLite[("SQLite Database<br/>bcrypt PIN Hashing")]
        LLM["llama.cpp (Gemma 4 A2B Q4_K_M)<br/>127.0.0.1:8080"]
        TTS["Offline Voice Output<br/>(Spanish TTS & K'iche' Audio)"]
        HDMI["Classroom Display (HDMI)<br/>Question, Timer, Results & Audio"]
    end

    Students <-->|"Wi-Fi (DHCP)"| Router
    Router <-->|"Ethernet"| Nginx
    Nginx --> PWA
    Nginx <-->|"API & WebSockets Proxy"| FastAPI

    FastAPI <--> SymPy
    FastAPI <--> Pedagogy
    FastAPI <--> SQLite
    FastAPI <-->|"IPC / Local HTTP (127.0.0.1:8080)"| LLM
    FastAPI <--> TTS
    FastAPI <--> HDMI
```

---

## <a id="2-hardware-topology"></a>2. Hardware Topology

All components operate **100% offline** without WAN connectivity.

| Node | Hardware | Role & Responsibilities |
| :--- | :--- | :--- |
| **Core AI Appliance** | NVIDIA Jetson Orin Nano (8GB Unified RAM) | Hosts all software services: Nginx reverse proxy, static PWA hosting, FastAPI backend, `llama.cpp` LLM engine, offline Spanish TTS & K'iche' audio, SymPy validation, SQLite database, and direct HDMI classroom display/audio. |
| **Wireless AP** | GL.iNet GL-AR300M16 Router | Isolated local Access Point broadcasting SSID `TutorBox`, handling local DHCP IP assignments for student devices. |

---

## <a id="3-software--ai-stack"></a>3. Software & AI Stack

* **Backend**: Python 3.10+, FastAPI, WebSockets (real-time chat & room management), SQLite (with idempotent SQL migrations).
* **Frontend**: React / Vite Progressive Web App (PWA), mobile-first, hosted directly on the Jetson appliance via Nginx.
* **Deterministic Math Engine**: **SymPy** for all mathematical parsing, algebraic verification, and equivalence checking.
* **LLM Engine**: **Gemma 4 A2B** quantized to `Q4_K_M` running via `llama.cpp` (`llama-server`) bound strictly to `127.0.0.1:8080`.
* **Voice Output**: Dual-language offline neural **Text-to-Speech (TTS)** in **Spanish** and **K'iche'** (`quc_Latn`) running via ONNX Runtime (Piper-TTS / Sherpa-ONNX) for dynamic distractor explanations and audio feedback.
* **Student Input**: Mobile web clicker interface (A–D buttons) and physical ESP32 clickers (strictly zero voice/microphone input).

---

## <a id="4-system-constraints--guardrails"></a>4. System Constraints & Guardrails

1. **No LLM Math**: The LLM is strictly prohibited from evaluating mathematical accuracy. SymPy is the sole authority for verification.
2. **Containment Guardrail**: Before any LLM response is returned to the user, SymPy solves the mathematical problem. If the generated text contains the final solution or an equivalent symbolic answer, the response is intercepted and regenerated.
3. **Audio Feedback & >51% Rule**: Offline neural TTS only speaks explanations when >51% of participating students select a specific diagnostic distractor (remaining silent on correct answers or dispersed votes).
4. **Security & Privacy**: Student PINs are hashed using `bcrypt` and must never appear in plain text in the database, memory dumps, or log files.
5. **Memory Budget**: The 8GB unified memory on the Jetson Orin Nano is strictly budgeted to support **15–20 concurrent student sessions** without triggering Out-Of-Memory (OOM) failures.

---

## <a id="5-repository-structure"></a>5. Repository Structure

```text
TutorBox/
├── backend/      # FastAPI application, Socratic logic, SymPy engine, offline voice, SQLite DB
├── pwa/          # React/Vite Progressive Web App source code (hosted on Jetson)
├── infra/        # Systemd service definitions, Nginx reverse proxy configs, setup scripts
└── docs/         # Architecture specs, pedagogical state machine rules, API documentation
```

---

## <a id="6-technical-documentation"></a>6. Technical Documentation

* **[Documentation Portal](docs/README.md)**: Index and navigation hub for technical specifications.
* **[Database Schema & ER Model](docs/database-schema.md)**: SQLite schema dictionaries, indexes, and migration log.
* **[REST API Reference & Contracts](docs/api-reference.md)**: RBAC matrix, auth flows, error formats, and 18 endpoint specifications.
* **[ESP32 Clicker Transport Specification](docs/architecture/esp32-clicker-transport.md)**: Physical hardware, network transport, dual LEDs, and `VoteTransport` interface.
* **[Backend Developer Guide](backend/README.md)**: Backend installation, local execution, and testing guide.

---

## Next Steps

* **[Explore the Documentation Portal](docs/README.md)**: Deep dive into the database schema, API contracts, and architecture.
* **[Setup Backend Environment](backend/README.md)**: Local developer setup, virtual environment, and testing instructions.
