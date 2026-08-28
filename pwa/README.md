# TutorBox Frontend (PWA)

React / Vite Progressive Web App client hosted directly on the NVIDIA Jetson Orin Nano appliance.

> [TutorBox](../README.md) / **Frontend (PWA)** • [Documentation](../docs/README.md) • [API Reference](../docs/api-reference.md)

---

## 1. Components & Client Interfaces

* **Student Quiz Voting Interface (A–D)**: Lightweight mobile-first web client for real-time classroom quiz responses via local Wi-Fi.
* **Teacher Management Portal**: Mobile interface for teachers to launch quiz sessions, select topics, and monitor voting distribution.
* **Socratic Tutor Client**: Offline-capable conversational math practice interface with persistent local student state.
* **Offline Primary Games Host**: Local mirror of `primariaconk.uk` educational games with local error caching and opportunistic synchronization.

---

## 2. Architecture & Offline Design

* **Network Delivery**: Static compiled assets served locally by Nginx on the Jetson appliance over the isolated `TutorBox` AP.
* **Offline First**: Service Workers and Cache Storage APIs allow client applications to function smoothly during transient network drops.
* **Hardware Agnostic**: Built to communicate via standard HTTP and WebSocket endpoints, seamlessly interoperating alongside physical ESP32 clickers.

---

## Next Steps

* **[REST API Reference](../docs/api-reference.md)**: Explore endpoint contracts for frontend client integration.
* **[Documentation Portal](../docs/README.md)**: View the overarching documentation index.
* **[10-Week Engineering Roadmap](../docs/milestones/roadmap.md)**: View frontend deliverables scheduled across Weeks 2–10.
