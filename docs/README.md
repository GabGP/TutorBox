# TutorBox Technical Documentation

Welcome to the **TutorBox** technical documentation portal. This hub indexes architectural specifications, database schemas, migration runbooks, and modular REST API contracts for the offline edge AI educational appliance.

<div align="center">

| 🏠 [TutorBox](../README.md) | 📚 **Docs** | ⚙️ [Backend](../backend/README.md) | 📱 [PWA](../pwa/README.md) | 🔌 [Infra](../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Docs Hub** • **Quick Links:** [API Hub](api/README.md) • [Database Schema](database/README.md) • [Migrations](database/migrations.md) • [Roadmap](milestones/roadmap.md)

</div>

---

## Table of Contents
- [1. System Architecture & Appliance Modes](#1-system-architecture--appliance-modes)
- [2. Modular REST API Specification](#2-modular-rest-api-specification)
- [3. Database Engine & Migrations](#3-database-engine--migrations)
- [4. Hardware & Network Infrastructure](#4-hardware--network-infrastructure)
- [5. Engineering Milestones & Rotational Roadmap](#5-engineering-milestones--rotational-roadmap)
- [Next Steps](#next-steps)

---

## <a id="1-system-architecture--appliance-modes"></a>1. System Architecture & Appliance Modes

Core pedagogical, mathematical, and algorithmic specifications powering the three appliance modes:

* **[The Three Appliance Modes & Transversal Telemetry](architecture/three-modes.md)**: Operational overview of Classroom Quiz Mode, Socratic Tutor Mode, and Offline Primary Games Mode with unified error event telemetry.
* **[Diagnostic Distractors & Misconception Taxonomy](architecture/diagnostic-distractors.md)**: 4-domain curriculum taxonomy and 32 validated misconception slugs powering Quiz mode feedback, Socratic tutoring, and teacher reporting.
* **[Socratic Pedagogical Model & Containment](architecture/socratic-pedagogy.md)**: Pedagogical state machine, deterministic 4-level hint escalation ladder, and SymPy math containment guardrails.
* **[ESP32 Hardware Clicker Architecture & Transport](architecture/esp32-clicker-transport.md)**: Physical 4-button student clickers, delegated pairing workflow, dual RGB LED feedback state machine, and the hardware-agnostic `VoteTransport` interface.
* **[ESP32 Clicker Protocol — BLE Provisioning & Voting](architecture/esp32-protocol.md)**: How a clicker receives the classroom Wi-Fi and its device secret over Bluetooth from the always-on appliance, then authenticates and votes through the session API.
* **[Hardware Architecture & Offline Topology](architecture/hardware-topology.md)**: Hardware specifications for the isolated local Access Point and NVIDIA Jetson Orin Nano appliance (8GB Unified RAM budget).

---

## <a id="2-modular-rest-api-specification"></a>2. Modular REST API Specification

Authoritative contracts, request/response JSON schemas, and security rules for the FastAPI backend:

* **[REST API Gateway & Security Reference](api/README.md)**: Base URL, Bearer session sequence flow, Role-Based Access Control (RBAC) matrix, PIN rotation policies, anti-oracle ordering, and standard error formats.

### Domain Endpoint Specifications
| Subsystem | Specification Document | Primary Endpoints |
| :--- | :--- | :--- |
| **System & Health** | **[api/system.md](api/system.md)** | `GET /health` |
| **Authentication & Users** | **[api/auth.md](api/auth.md)** | `POST /auth/login`, `POST /auth/logout`, `/users/*` (signup, me, pin, username) |
| **Staff Administration** | **[api/staff.md](api/staff.md)** | `GET/POST /staff/users`, PIN resets, soft-delete, account recovery, audit logs |
| **Hardware Devices** | **[api/devices.md](api/devices.md)** | `GET/POST /staff/devices`, device assignment, unassign, fleet delete |
| **Quiz Question Bank** | **[api/quiz.md](api/quiz.md)** | Curriculum topics, JSON Schema, SymPy validate, SLM generation, question bank |
| **Quiz Sessions & Voting** | **[api/sessions.md](api/sessions.md)** | Session match lifecycle, voting countdown, first-press vote persistence, >51% Rule |

---

## <a id="3-database-engine--migrations"></a>3. Database Engine & Migrations

Technical reference for the local SQLite edge database engine:

* **[Database Schema & ER Model](database/README.md)**: Engine pragmas (WAL, busy timeout, foreign keys), full Mermaid Entity-Relationship (ER) diagram, complete data dictionary for all 11 tables, performance B-tree indexes, and data lifecycle policies (soft-delete, last-admin guard, clicker unlinking).
* **[Database Migrations Playbook & Changelog](database/migrations.md)**: Complete chronological changelog for migrations `001` through `010`, migration authoring workflow, idempotency validation, and edge backup runbook.

---

## <a id="4-hardware--network-infrastructure"></a>4. Hardware & Network Infrastructure

Setup guides and runbooks for offline edge deployment:

* **[Infrastructure Hub](../infra/README.md)**: Overview of classroom hardware topology and networking.
* **[GL.iNet GL-AR300M16 Initial Setup](../infra/glinet/initial.md)**: 6-step provisioning runbook for isolated classroom AP, static DHCP leases, and 4-layer WAN disconnection.
* **[Hardware Topology & Memory Budget](architecture/hardware-topology.md)**: Jetson Orin Nano 8GB unified memory allocation across SLM, TTS, FastAPI, and SQLite.

---

## <a id="5-engineering-milestones--rotational-roadmap"></a>5. Engineering Milestones & Rotational Roadmap

Engineering schedule and weekly deliverables:

* **[10-Week Engineering Roadmap](milestones/roadmap.md)**: Master Gantt chart, weekly Pilot/Copilot rotation rules, and milestone work packages.
* **[Week 1 Milestone Synthesis](milestones/week-1-auth-storage.md)**: Appliance baseline, SQLite storage, authentication, and security proofs.
* **[Week 2 Milestone Tracking](milestones/week-2-quiz-contract.md)**: Quiz JSON Schema contract, SymPy validation, 32 diagnostic distractors, and question bank.
* **[Week 3 Milestone Synthesis](milestones/week-3-session-engine.md)**: Real-time session engine, deterministic >51% Rule evaluator, first-press locking, and REST API.

---

## Next Steps

* **[API Gateway & Hub](api/README.md)**: Explore the endpoint contracts and schemas.
* **[Database Schema Reference](database/README.md)**: Inspect SQLite tables and relationships.
* **[Backend Developer Guide](../backend/README.md)**: Setup local virtual environment, run test suites, and review quality gates.
