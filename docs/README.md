# TutorBox Technical Documentation

Welcome to the **TutorBox** documentation portal. This directory contains detailed architectural specifications, database schemas, and REST API contract documentation for the offline edge AI educational platform.

<div align="center">

| 🏠 [TutorBox](../README.md) | 📚 **Docs** | ⚙️ [Backend](../backend/README.md) | 📱 [PWA](../pwa/README.md) | 🔌 [Infra](../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Docs** › **Documentation Hub** • **Quick Links:** [API Reference](api-reference.md) • [Database Schema](database-schema.md) • [Roadmap](milestones/roadmap.md) • [Three Modes](architecture/three-modes.md)

</div>

---

## Table of Contents
- [1. Core Technical References](#1-core-technical-references)
  - [Database Schema & ER Model](#database-schema--er-model)
  - [REST API Reference & Contracts](#rest-api-reference--contracts)
- [2. System Architecture & Modes](#2-system-architecture--modes)
  - [The Three Appliance Modes & Transversal Telemetry](#the-three-appliance-modes--transversal-telemetry)
  - [Hardware Architecture & Offline Topology](#hardware-architecture--offline-topology)
  - [ESP32 Hardware Clicker Architecture & Transport](#esp32-hardware-clicker-architecture--transport)
  - [Socratic Pedagogical Model & Containment](#socratic-pedagogical-model--containment)
- [3. Project Milestones & Roadmap](#3-project-milestones--roadmap)
  - [10-Week Engineering Roadmap](#10-week-engineering-roadmap)
  - [Week 1 Milestone Synthesis](#week-1-milestone-synthesis)
- [Next Steps](#next-steps)

---

## <a id="1-core-technical-references"></a>1. Core Technical References

### <a id="database-schema--er-model"></a>[Database Schema & ER Model](database-schema.md)
Complete reference for the local SQLite edge database engine, including ER diagrams, data dictionary, performance indexes, and migration history.

### <a id="rest-api-reference--contracts"></a>[REST API Reference & Contracts](api-reference.md)
Integration contracts and communication protocols for the FastAPI backend, covering authentication flows, RBAC matrix, rate limiting, and unified error formats.

---

## <a id="2-system-architecture--modes"></a>2. System Architecture & Modes

### <a id="the-three-appliance-modes--transversal-telemetry"></a>[The Three Appliance Modes & Transversal Telemetry](architecture/three-modes.md)
Overview of the three operational modes (Classroom Quiz, Socratic Tutor, and Offline Primary Games) and the transversal error logging system.

### <a id="hardware-architecture--offline-topology"></a>[Hardware Architecture & Offline Topology](architecture/hardware-topology.md)
Hardware specifications for the isolated local Access Point and NVIDIA Jetson Orin Nano appliance, including the 8GB Unified RAM memory budget.

### <a id="esp32-hardware-clicker-architecture--transport"></a>[ESP32 Hardware Clicker Architecture & Transport](architecture/esp32-clicker-transport.md)
Physical 4-button student clickers, delegated pairing workflow, dual RGB LED feedback state machine, and the hardware-agnostic `VoteTransport` interface.

### <a id="socratic-pedagogical-model--containment"></a>[Socratic Pedagogical Model & Containment](architecture/socratic-pedagogy.md)
Pedagogical dialogue rules, deterministic 4-level hint escalation ladder, and SymPy math containment guardrails.

---

## <a id="3-project-milestones--roadmap"></a>3. Project Milestones & Roadmap

### <a id="10-week-engineering-roadmap"></a>[10-Week Engineering Roadmap](milestones/roadmap.md)
Complete 10-week engineering schedule, weekly Pilot/Copilot rotation rules, and milestone deliverables.

### <a id="week-1-milestone-synthesis"></a>[Week 1 Milestone Synthesis](milestones/week-1-auth-storage.md)
Architecture review, security proofs, and verification summary for the Week 1 baseline.

---

## Next Steps

* **[The Three Appliance Modes](architecture/three-modes.md)**: Understand the Quiz, Tutor, and Offline Games architecture.
* **[10-Week Engineering Roadmap](milestones/roadmap.md)**: Explore the Week 2 Quiz Contract & Diagnostic Distractor requirements.
* **[Backend Developer Guide](../backend/README.md)**: Local developer setup, virtual environment, and testing instructions.
