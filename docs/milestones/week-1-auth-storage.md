# Week 1 Milestone: Appliance Baseline & Storage Infrastructure

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Docs** › **Milestones** › **Week 1 Milestone** • **Related:** [Engineering Roadmap](roadmap.md)

</div>

---

This document summarizes the technical deliverables, architectural implementations, and quality metrics achieved during the **Week 1 Milestone** by both **Student A** and **Student B**.

---

## 1. Executive Summary & Verification Metrics
* **Status**: **100% Complete & Green (Both Student A and Student B)**
* **Backend Test Suite**: **134 / 134 passing tests**
* **Statement Coverage**: **100.00% coverage** across all 25 source files (`pyproject.toml` enforces `--cov-fail-under=80`).
* **Linter & Formatter**: **0 errors, 0 warnings** (`ruff check backend/` and `ruff format --check backend/`).
* **Modularity Compliance**: **100% of source files $\le 149$ LoC** ($\le 150$ LoC rule) and **100% of test files $\le 295$ LoC** ($\le 300$ LoC rule).
* **Hardware & Appliance Baseline**:
  * Jetson Orin Nano running headless JetPack on NVMe in 25W mode with persistent `jetson_clocks`.
  * Idle system RAM footprint verified at **$\le 1.0$ GB RSS**.
  * GL-AR300M16 router configured as isolated local classroom AP without WAN routing.

---

## 2. Implemented Subsystems by Lead

### A. Student A: Backend, Database & CI Infrastructure
1. **SQLite Database & Migrations (001–006)**:
   * Engine Pragmas: `PRAGMA foreign_keys = ON;`, `PRAGMA journal_mode = WAL;`, `PRAGMA busy_timeout = 5000;`.
   * Migrations: `001_initial_schema.sql` through `006_add_audit_logs.sql`.
2. **Security & RBAC Infrastructure**:
   * Multi-role hierarchy (`student`, `teacher`, `admin`).
   * UUIDv4 Bearer session token management.
   * Forced PIN rotation gating on `/users/me/pin`.
   * Anti-oracle cryptographic verification order.
   * Dual rate limiting (exponential lockout + sliding window).
   * 7 verified security proofs against plaintext credential leakage.
3. **13 Production REST Endpoints**:
   * Health check, login/logout, user profile & credentials, staff user management, PIN reset, soft deletion & recovery, audit trail.

### B. Student B: Appliance Provisioning, Hardware & Networking
1. **Jetson Orin Nano Base Configuration**:
   * Clean OS installation of JetPack flashed directly to high-speed NVMe storage.
   * Desktop GUI disabled for headless operation to conserve memory.
   * Configured for maximum performance in 25W mode with persistent `jetson_clocks`.
   * Idle system verified under memory budget ($\le 1.0$ GB RSS).
2. **Classroom Local Access Point (GL-AR300M16)**:
   * Isolated local network broadcasting SSID `TutorBox` with local DHCP pool.
   * WAN interface disconnected/disabled to enforce 100% offline isolation.
