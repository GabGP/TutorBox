# TutorBox Technical Documentation

Welcome to the **TutorBox** documentation portal. This directory contains detailed architectural specifications, database schemas, and REST API contract documentation for the offline edge AI educational platform.

> [TutorBox](../README.md) / **Documentation** • [Backend](../backend/README.md) • [Frontend](../pwa/README.md) • [Infrastructure](../infra/README.md)

---

## Table of Contents
- [1. Technical Guides & Specifications](#1-technical-guides--specifications)
  - [Database Schema & ER Model](#database-schema--er-model)
  - [REST API Reference & Contracts](#rest-api-reference--contracts)
- [2. Architectural Roadmap](#2-architectural-roadmap)
- [Next Steps](#next-steps)

---

## 1. Technical Guides & Specifications

### Database Schema & ER Model
Complete documentation for the SQLite edge database engine in **[`database-schema.md`](database-schema.md)**:
* **Engine Configuration**: WAL mode, foreign key enforcement, and busy timeout pragmas.
* **Mermaid Entity-Relationship (ER) Diagram**: Visual model of `users`, `sessions`, `turn_logs`, `audit_logs`, and `schema_migrations`.
* **Data Dictionaries**: Field-by-field definitions, constraints, and defaults for all 5 schema tables.
* **Performance Indexes**: Optimization strategies for edge NVMe/eMMC storage.
* **Data Lifecycle Policies**: Soft-deletion, username freeing, telemetry preservation, and the Last-Admin Guard.
* **Migration Changelog**: Full record of migrations `001` through `006`.

---

### REST API Reference & Contracts
Integration contracts and communication protocols for the FastAPI backend in **[`api-reference.md`](api-reference.md)**:
* **System Overview & Base URL**: Edge appliance network configuration (`http://<appliance-ip>:8000`).
* **Authentication & Session Flow**: Bearer session tokens (`Authorization: Bearer <uuid4>`) with interactive Mermaid sequence diagram.
* **Role-Based Access Control (RBAC) Matrix**: Permissions grid across `student`, `teacher`, and `admin` roles.
* **Security Policies & Protections**: Forced PIN rotation allowlists, anti-oracle validation order, and dual-layer rate limiting (exponential lockout + sliding window).
* **Unified Error Matrix**: Standardized error schema and HTTP status code triggers (`401`, `403`, `404`, `409`, `422`, `429`).
* **Detailed Endpoint Contracts (13 Routes)**:
  * **System & Health**: `GET /health`
  * **Authentication**: `POST /login`, `POST /logout`
  * **User Self-Service**: `POST /signup`, `GET /users/me`, `PATCH /users/me/pin`, `PATCH /users/me/username`
  * **Staff Administration**: `GET /users`, `POST /users`, `POST /users/{id}/reset-pin`, `DELETE /users/{id}`, `POST /users/{id}/recover`
  * **System Audit**: `GET /audit-logs`

---

## 2. Architectural Roadmap

* **Pedagogical State Machine**: Socratic ladder escalation logic and conversation tree rules.
* **SymPy Validation Engine**: Deterministic mathematical syntax checking and LLM hallucination containment guardrails.
* **K'iche' Speech Recognition (ASR)**: Offline Meta Omnilingual ASR 300M CTC int8 (`sherpa-onnx`) pipeline.
* **Hardware & Network Topology**: NVIDIA Jetson Orin Nano + BeagleBone Black (BBB) USB-CDC / Wi-Fi mesh interaction.

---

## Next Steps

* **[Database Schema Reference](database-schema.md)**: Deep dive into the SQLite ER diagram and table data dictionaries.
* **[REST API Reference](api-reference.md)**: Review endpoint contracts, schemas, and RBAC matrix.
* **[Backend Developer Guide](../backend/README.md)**: Local developer setup, virtual environment, and testing instructions.
