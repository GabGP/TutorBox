# ESP32 Clicker Transport

How a physical clicker's vote reaches the session engine. This page is a short map. The parts, the wiring, the flashing steps, the lights and the troubleshooting are in the [Clicker Firmware guide](../../firmware/clicker/README.md).

<div align="center">

| 🏠 [Utz'tutor](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › **Architecture** › **ESP32 Clicker Transport** • **Related:** [Clicker Firmware](../../firmware/clicker/README.md) • [ESP32 Clicker Protocol](esp32-protocol.md) • [Devices API](../api/devices.md) • [Hardware Topology](hardware-topology.md)

</div>

---

## Table of Contents
- [1. What a Clicker Is](#1-what-a-clicker-is)
- [2. How a Vote Travels](#2-how-a-vote-travels)
- [3. The `VoteTransport` Seam](#3-the-votetransport-seam)
- [4. Where the Details Are](#4-where-the-details-are)
- [5. Designed and Not Built](#5-designed-and-not-built)

---

## <a id="1-what-a-clicker-is"></a>1. What a Clicker Is

A clicker is a handheld with four answer buttons (A, B, C, D), a power button and one RGB light, built on an ESP32-C3 Super Mini. It is for the **Classroom Quiz Mode**, for young students who should not have to type a username and a PIN on a small screen.

The teacher assigns each clicker to a student in **Clickers** on `/maestro/`. The clicker then votes as that student until it is reassigned.

---

## <a id="2-how-a-vote-travels"></a>2. How a Vote Travels

The clicker uses the same REST API as the phones, over the classroom Wi-Fi. The backend has no clicker-only vote path.

| Step | What the clicker does | Reference |
| :--- | :--- | :--- |
| Wi-Fi | Joins `Utz'tutor` with the name and password compiled into its firmware. | [Firmware §6](../../firmware/clicker/README.md#6-install-the-software-and-flash) |
| Login | Sends `POST /api/v1/devices/auth` with its device id and the secret it made itself. The first login registers the clicker; after that the answer is a token that votes as the assigned student. | [Devices API](../api/devices.md#post-devices-auth) |
| Wait | Polls `GET /api/v1/session/current` every second to see whether a question is open. | [Sessions API](../api/sessions.md#get-session-current) |
| Vote | Sends `POST /api/v1/session/{session_id}/vote`, the endpoint the phones use. | [Sessions API](../api/sessions.md#post-session-vote) |
| Presence | Sends `POST /api/v1/presence/heartbeat` every 5 seconds with its signal and battery level, so the lobby lists it as connected. | [Presence API](../api/presence.md#post-presence-heartbeat) |

Two things are set once per clicker:

* **Device id.** The clicker computes it from its MAC address (`ESP32-A4CF12`).
* **Device secret.** The clicker makes it on its first boot and keeps it in its flash. The TutorBox keeps only the SHA-256 digest of the first one it receives ([Firmware §7](../../firmware/clicker/README.md#7-first-power-on-and-assigning-a-student)).

---

## <a id="3-the-votetransport-seam"></a>3. The `VoteTransport` Seam

The guardrail is that the session engine knows nothing about how a vote arrived. Early diagrams drew this as a Python class hierarchy (`VoteTransport`, with one subclass per client). That was not built: an ESP32 and a phone browser are separate machines and cannot share a Python object.

The seam is the wire contract, `POST /api/v1/session/{session_id}/vote`:

* **The server labels each vote from the caller's session.** A token issued to a clicker records `hardware` with that clicker's id. Any other token records `web`. The request body cannot choose the label.
* **The session engine has no hardware code.** No file under `backend/src/modes/` changed when the clickers were added.
* **The first press locks across transports.** A student who votes on a clicker and then on a phone gets `409`.
* **A clicker's token can only vote and send the heartbeat.** Every other endpoint refuses it with `403` ([Clicker Token Revocation](../api/devices.md#clicker-token-revocation) lists what ends the token).

`backend/tests/api/session/test_session_fleet_hardware.py` checks this with 15 simulated clickers and 15 phones in the same match.

---

## <a id="4-where-the-details-are"></a>4. Where the Details Are

| Topic | Document |
| :--- | :--- |
| Parts, pin map, wiring, power | [Clicker Firmware §2 to §5](../../firmware/clicker/README.md#2-parts-per-clicker) |
| Flashing, first power-on, assigning a student | [Clicker Firmware §6 and §7](../../firmware/clicker/README.md#6-install-the-software-and-flash) |
| What each light means | [Clicker Firmware §8](../../firmware/clicker/README.md#8-what-the-light-means) |
| Bench test and troubleshooting | [Clicker Firmware §9 and §10](../../firmware/clicker/README.md#9-bench-test-checklist) |
| Code layout, and what the clicker does with each HTTP status | [Clicker Firmware §11](../../firmware/clicker/README.md#11-how-the-code-is-organized) |
| Firmware tests on a PC | [Clicker Firmware §12](../../firmware/clicker/README.md#12-testing-without-hardware) |
| Setup and voting protocol, failure modes | [ESP32 Clicker Protocol](esp32-protocol.md) |
| Assign, delete, enrollment and login endpoints | [Devices API](../api/devices.md) |
| Lobby presence, signal and battery | [Presence API](../api/presence.md) |
| What is built and what waits for hardware | [Week 7 Milestone](../milestones/week-7-esp32-clickers.md) |

---

## <a id="5-designed-and-not-built"></a>5. Designed and Not Built

Earlier versions of this page described these. None of them exists in the code.

* **Bluetooth provisioning from the appliance.** It was designed in [ESP32 Clicker Protocol](esp32-protocol.md) and dropped on 2026-10-13.
* **A setup soft-AP** that the clicker would open when it cannot find the classroom Wi-Fi.
* **ESP-NOW** with a USB receiver on the Jetson.
* **A `voltage_mv` field** in the heartbeat. The clicker sends `rssi` and `battery_pct`.
