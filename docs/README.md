# TutorBox Technical Documentation

Welcome to the **TutorBox** documentation portal. This directory contains detailed architectural specifications, database schemas, and REST API contract documentation for the offline edge AI educational platform.

<div align="center">

| 🏠 [TutorBox](../README.md) | 📚 **Docs** | ⚙️ [Backend](../backend/README.md) | 📱 [PWA](../pwa/README.md) | 🔌 [Infra](../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Docs** › **Documentation Hub** • **Quick Links:** [API Reference](api-reference.md) • [Database Schema](database-schema.md) • [Roadmap](milestones/roadmap.md) • [Three Modes](architecture/three-modes.md)

</div>

---

## Table of Contents
- [TutorBox Technical Documentation](#tutorbox-technical-documentation)
  - [Table of Contents](#table-of-contents)
  - [1. Core Technical References](#1-core-technical-references)
    - [Database Schema \& ER Model](#database-schema--er-model)
    - [REST API Reference \& Contracts](#rest-api-reference--contracts)
  - [2. System Architecture \& Modes](#2-system-architecture--modes)
    - [The Three Appliance Modes \& Transversal Telemetry](#the-three-appliance-modes--transversal-telemetry)
    - [Hardware Architecture \& Offline Topology](#hardware-architecture--offline-topology)
    - [ESP32 Hardware Clicker Architecture \& Transport](#esp32-hardware-clicker-architecture--transport)
    - [Socratic Pedagogical Model \& Containment](#socratic-pedagogical-model--containment)
  - [3. Project Milestones \& Roadmap](#3-project-milestones--roadmap)
    - [10-Week Engineering Roadmap](#10-week-engineering-roadmap)
    - [Week 1 Milestone Synthesis](#week-1-milestone-synthesis)
  - [Next Steps](#next-steps)

---

## <a id="1-core-technical-references"></a>1. Core Technical References

### <a id="database-schema--er-model"></a>[Database Schema & ER Model](database-schema.md)
Complete documentation for the SQLite edge database engine in **[`database-schema.md`](database-schema.md)**:
* **Engine Configuration**: WAL mode, foreign key enforcement, and busy timeout pragmas.
* **Mermaid Entity-Relationship (ER) Diagram**: Visual model of `users`, `devices`, `sessions`, `turn_logs`, `audit_logs`, and `schema_migrations`.
* **Data Dictionaries**: Field-by-field definitions, constraints, and defaults for all schema tables.
* **Performance Indexes**: Optimization strategies for edge NVMe/eMMC storage.
* **Data Lifecycle Policies**: Soft-deletion, username freeing, device unlinking, telemetry preservation, and the Last-Admin Guard.
* **Migration Changelog**: Full record of migrations.

---

### <a id="rest-api-reference--contracts"></a>[REST API Reference & Contracts](api-reference.md)
Integration contracts and communication protocols for the FastAPI backend in **[`api-reference.md`](api-reference.md)**:
* **System Overview & Base URL**: Edge appliance network configuration (`http://<appliance-ip>:8000`).
* **Authentication & Session Flow**: Bearer session tokens (`Authorization: Bearer <uuid4>`) with interactive Mermaid sequence diagram.
* **Role-Based Access Control (RBAC) Matrix**: Permissions grid across `student`, `teacher`, and `admin` roles.
* **Security Policies & Protections**: Forced PIN rotation allowlists, anti-oracle validation order, and dual-layer rate limiting (exponential lockout + sliding window).
* **Unified Error Matrix**: Standardized error schema and HTTP status code triggers (`401`, `403`, `404`, `409`, `422`, `429`).
* **Detailed Endpoint Contracts (18 Routes)**:
  * **System & Health**: `GET /health`
  * **Authentication**: `POST /login`, `POST /logout`
  * **User Self-Service**: `POST /signup`, `GET /users/me`, `PATCH /users/me/pin`, `PATCH /users/me/username`
  * **Staff Administration**: `GET /users`, `POST /users`, `POST /users/{user_id}/reset-pin`, `DELETE /users/{user_id}`, `POST /users/{user_id}/recover`
  * **System Audit**: `GET /audit-logs`
  * **Hardware Fleet & Pairing**: `GET /devices`, `POST /devices`, `POST /devices/{device_id}/assign`, `POST /devices/{device_id}/unassign`, `DELETE /devices/{device_id}`

---

## <a id="2-system-architecture--modes"></a>2. System Architecture & Modes

### <a id="the-three-appliance-modes--transversal-telemetry"></a>[The Three Appliance Modes & Transversal Telemetry](architecture/three-modes.md)
* **Mode 1: Classroom Quiz**: Teacher-led classroom quiz with diagnostic distractors and the >51% offline audio explanation rule.
* **Mode 2: Socratic Tutor**: After-class mobile math tutoring with SymPy containment.
* **Mode 3: Offline Primary Games**: `primariaconk.uk` games with opportunistic error log synchronization.
* **Unified Analytics**: Transversal error concept logging generating a weekly teacher remediation report.

### <a id="hardware-architecture--offline-topology"></a>[Hardware Architecture & Offline Topology](architecture/hardware-topology.md)
* **Offline Network Layout**: Isolated Access Point (GL.iNet) and Jetson Orin Nano Core Appliance.
* **Unified Memory Budget**: 8GB RAM allocation breakdown for concurrent multi-mode operations.

### <a id="esp32-hardware-clicker-architecture--transport"></a>[ESP32 Hardware Clicker Architecture & Transport](architecture/esp32-clicker-transport.md)
* **Delegated Authentication**: Eliminating credentials for primary school students via teacher-managed 1:1 clicker pairing.
* **Abstract `VoteTransport`**: Decoupled interface supporting both Web PWA clients and ESP32 hardware clickers.
* **Dual Feedback Loop**: RGB LED hardware state machine (Yellow TX $\to$ Green confirmed / Red error) and HDMI classroom display.

### <a id="socratic-pedagogical-model--containment"></a>[Socratic Pedagogical Model & Containment](architecture/socratic-pedagogy.md)
* **Socratic Dialogue Principle**: Never revealing direct solutions; guiding students through misconception diagnosis.
* **Hint Escalation Ladder**: Deterministic 4-level hint progression ($0 \to 3$).

---

## <a id="3-project-milestones--roadmap"></a>3. Project Milestones & Roadmap

### <a id="10-week-engineering-roadmap"></a>[10-Week Engineering Roadmap](milestones/roadmap.md)
Sequential delivery schedule balancing development between Student A and Student B with weekly Pilot / Copilot rotations.

### <a id="week-1-milestone-synthesis"></a>[Week 1 Milestone Synthesis](milestones/week-1-auth-storage.md)
Detailed post-milestone review covering 100% test coverage, zero linter warnings, RBAC proofs, and modularity verification.

---

## Next Steps

* **[The Three Appliance Modes](architecture/three-modes.md)**: Understand the Quiz, Tutor, and Offline Games architecture.
* **[10-Week Engineering Roadmap](milestones/roadmap.md)**: Explore the Week 2 Quiz Contract & Diagnostic Distractor requirements.
* **[Backend Developer Guide](../backend/README.md)**: Local developer setup, virtual environment, and testing instructions.
