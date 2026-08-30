# ESP32 Hardware Clicker Architecture & Transport Specification

Comprehensive engineering specification for the **TutorBox Physical Clicker Subsystem**, detailing hardware design, network transport, AP association, telemetry monitoring, teacher pairing lifecycle, and the abstract `VoteTransport` interface.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Docs** › **Architecture** › **ESP32 Clicker Transport** • **Related:** [Hardware Topology](hardware-topology.md) • [Three Modes](three-modes.md) • [Database Schema](../database-schema.md)

</div>

---

> [!NOTE]
> **Work in Progress & Tentative Engineering Blueprint**:
> This document represents an evolving architectural specification prepared ahead of the hardware development milestones. The interface contracts, transport protocols, telemetry payloads, and hardware benchmarks will be expanded and refined during **Week 3 (Session Engine & Abstract Transport)** and finalized in **Week 7 (ESP32 Hardware Clickers & Fleet Testing)**.

---

## Table of Contents
- [1. Subsystem Overview & Pedagogical Purpose](#1-subsystem-overview--pedagogical-purpose)
- [2. Hardware Specifications & Bill of Materials](#2-hardware-specifications--bill-of-materials)
- [3. Wi-Fi AP Association & Provisioning Mechanisms](#3-wi-fi-ap-association--provisioning-mechanisms)
- [4. End-to-End Communication Flow & Pairing Model](#4-end-to-end-communication-flow--pairing-model)
- [5. Abstract `VoteTransport` Architecture (Week 3 & Week 7 Bridge)](#5-abstract-votetransport-architecture-week-3--week-7-bridge)
- [6. Visual Feedback & Dual LED State Machines](#6-visual-feedback--dual-led-state-machines)
- [7. Fleet Health Telemetry & Teacher PWA Dashboard](#7-fleet-health-telemetry--teacher-pwa-dashboard)
- [8. Concurrency, Latency & Edge Case Resilience](#8-concurrency-latency--edge-case-resilience)
- [9. Implementation Roadmap & Milestones](#9-implementation-roadmap--milestones)
- [Next Steps](#next-steps)

---

## 1. Subsystem Overview & Pedagogical Purpose

In rural and primary classroom environments (grades 1–6, ages 6–12), asking students to type alphanumeric usernames and PINs on small screens is a significant pedagogical friction point.

The **TutorBox Physical Clicker Subsystem** provides a dedicated, tactile 4-button hardware alternative (A, B, C, D) for the **Classroom Quiz Mode**:
* **Zero Student Setup**: Students pick up their numbered clicker (e.g. `#5`) and immediately participate.
* **Delegated Authorization**: The teacher links clicker IDs to student accounts via the Teacher PWA in seconds.
* **Dual Feedback Loop**: Both the handheld RGB LED and the classroom HDMI projector visually confirm vote ingestion.
* **Centralized Fleet Health**: Battery levels and connectivity are automatically reported to the teacher's dashboard, removing hardware management cognitive load from young students.
* **Decoupled Engine**: Built on the abstract `VoteTransport` interface, allowing the session engine to process votes identically regardless of whether the source is a mobile web client (PWA) or an ESP32 hardware clicker.

---

## 2. Hardware Specifications & Bill of Materials

```mermaid
graph LR
    subgraph ESP32Node ["ESP32 Physical Clicker Node"]
        MCU["ESP32-C3 / WROOM-32<br/>(2.4GHz 802.11 b/g/n Wi-Fi)"]
        BtnA["Button A (GPIO 18)"]
        BtnB["Button B (GPIO 19)"]
        BtnC["Button C (GPIO 21)"]
        BtnD["Button D (GPIO 22)"]
        VoteLED["Vote RGB LED<br/>(GPIO 8)"]
        NetLED["Wi-Fi / Status LED<br/>(GPIO 9)"]
        BattDiv["Battery ADC Divider<br/>(GPIO 0 / ADC1)"]
        Power["3.7V 500mAh LiPo / 2x AAA<br/>+ TP4056 Charger & 3.3V LDO"]

        BtnA --> MCU
        BtnB --> MCU
        BtnC --> MCU
        BtnD --> MCU
        MCU --> VoteLED
        MCU --> NetLED
        BattDiv --> MCU
        Power --> BattDiv
        Power --> MCU
    end
```

### Component Breakdown:
| Component | Specification | Purpose |
| :--- | :--- | :--- |
| **Microcontroller (MCU)** | ESP32-C3-MINI-1 or ESP32-WROOM-32D | 160MHz RISC-V/Xtensa core, 2.4GHz Wi-Fi, ultra-low power deep sleep. |
| **Input Buttons** | 4x Momentary Tactile Push Buttons (12mm) | Physical options A, B, C, D with 200ms software debounce. |
| **Vote / Feedback LED** | 1x Common-Cathode RGB LED or WS2812B (GPIO 8) | Handheld voting status (transmitting, confirmed, error). |
| **Status / Wi-Fi LED** | 1x Dedicated Blue/Red LED (GPIO 9) | AP association progress and local hardware fault indicator. |
| **Battery Sense (ADC)** | 2x 100kΩ resistor divider to ADC (GPIO 0) | Measures battery voltage ($3.0\text{V} - 4.2\text{V}$) for telemetry. |
| **Power & Charging** | 3.7V 500mAh LiPo battery + TP4056 USB-C module | 8+ hours of continuous classroom active usage per charge. |
| **Physical Enclosure** | 3D-printed PLA / Injection Molded Case | Durable casing with visible laser-engraved/sticker number (e.g. `1`..`30`). |

---

## 3. Wi-Fi AP Association & Provisioning Mechanisms

A common question in offline hardware design is: **How does each physical clicker connect to the appliance's local Wi-Fi Access Point without a screen or keyboard?**

TutorBox evaluates three connectivity strategies, with **Factory Fleet Provisioning** serving as the primary design:

```mermaid
graph TD
    Factory(["1. Factory Flashing Stage"]):::factory --> FlashNVS["Burn SSID 'TutorBox', WPA2 Key & device_id into NVS Flash"]

    FlashNVS --> PowerOn(["2. Classroom Power-On"]):::student
    PowerOn --> Boot["ESP32 Cold Boot (< 0.8s) & Load NVS Credentials"]
    Boot --> ScanAP{"TutorBox AP<br/>Found within 5s?"}

    ScanAP -- "Yes (Normal Mode)" --> Associate["Auto-Associate via 802.11 b/g/n"]
    Associate --> DHCP["Obtain DHCP Lease (192.168.8.x)"]
    DHCP --> Ready(["3. Online & Ready for Voting"]):::success

    ScanAP -- "No (Fallback Mode)" --> SoftAP["Launch Config Soft-AP 'TutorBox-Clicker-Setup'"]
    SoftAP --> TeacherPortal["Teacher Configures New Wi-Fi via PWA Portal"]
    TeacherPortal --> SaveNVS["Save New Credentials to NVS & Auto-Reboot"]
    SaveNVS --> Boot

    subgraph EspNowOption ["Alternative Protocol: ESP-NOW (Week 7 Evaluation)"]
        RawPress["Student Press -> Raw 2.4GHz Radio Packet"]
        JetsonDongle["ESP32 USB Receiver Dongle on Jetson"]
        FastApiPipe["Forward directly to FastAPI Session Engine (< 5ms)"]
        RawPress --> JetsonDongle --> FastApiPipe
    end

    classDef factory fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
    classDef student fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#e65100;
    classDef success fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;
```

### 1. Primary Strategy: Appliance Factory Provisioning (Zero-Touch)
* **Pre-Shared Appliance Network**: Every TutorBox appliance kit includes a pre-configured router (GL-AR300M16) with fixed network parameters:
  - **SSID**: `TutorBox`
  - **WPA2 Pre-Shared Key**: Configured in appliance manufacturing
  - **Backend Gateway**: `192.168.8.1:8000` (static router IP)
* **Firmware Embedding**: When the batch of 30 clickers is flashed in Week 7, the Wi-Fi credentials, gateway IP, and unique `device_id` (e.g. `"1"`, `"2"`, `"ESP32_01"`) are burned into the ESP32 Non-Volatile Storage (NVS).
* **Classroom Experience**: The student simply turns on the device switch. The ESP32 boots in $< 0.8\text{s}$, automatically associates to the `TutorBox` AP, and enters the low-power listening loop. **Zero configuration is required in the classroom.**

### 2. Secondary Strategy: Captive Portal / BLE Provisioning Fallback
* If the appliance router SSID or security key is modified:
  - If the ESP32 fails to connect after 5 seconds, it enters provisioning mode (blinking blue).
  - It hosts a temporary setup soft-AP (`TutorBox-Clicker-Config`) allowing the teacher or administrator to update network credentials once from a mobile phone browser.

### 3. Alternative Protocol: ESP-NOW Direct Radio Broadcast (Week 7 Exploration)
* **How It Works**: ESP-NOW is a connectionless 2.4GHz protocol developed by Espressif that transmits raw peer-to-peer radio packets without Wi-Fi association or IP stack overhead.
* **Benefits**:
  - Eliminates Wi-Fi association times (transmission takes $< 5\text{ms}$).
  - Bypasses router client association limits (supports 100+ concurrent clickers without saturating the router's DHCP pool).
  - A small ESP32 USB dongle connected to the Jetson Orin Nano receives raw radio packets and forwards them to FastAPI via local serial or loopback.

---

## 4. End-to-End Communication Flow & Pairing Model

TutorBox utilizes a **Teacher-Delegated Trust Model** to eliminate student authentication barriers on hardware clickers while maintaining strict tenant isolation.

```mermaid
sequenceDiagram
    autonumber
    actor Teacher as Teacher (PWA Portal)
    participant API as FastAPI Backend (:8000)
    participant DB as SQLite DB (`devices`)
    actor Student as Student (Clicker #1)
    participant ESP32 as ESP32 Clicker
    participant Screen as Classroom HDMI Display

    Note over Teacher,DB: Step 1: Teacher Pairing (In-Band Auth)
    Teacher->>API: POST /devices/1/assign {"user_id": 12} (Bearer Token)
    API->>DB: UPDATE devices SET assigned_user_id = 12 WHERE device_id = '1'
    API-->>Teacher: 200 OK {"device_id": "1", "assigned_user_id": 12, "assigned_username": "juan_p"}

    Note over Student,Screen: Step 2: Quiz Turn & Voting + Telemetry
    Teacher->>API: POST /quiz/session/start-question (Timer Opens)
    API->>Screen: Render Question & A-D Options on HDMI Display
    Student->>ESP32: Presses Button 'B'
    ESP32->>ESP32: Vote LED = BLINK YELLOW (TX in-flight)
    ESP32->>API: POST /vote/device {"device_id": "1", "choice": "B", "battery_pct": 88, "rssi": -55}
    API->>DB: SELECT assigned_user_id FROM devices WHERE device_id = '1'
    Note over API: Resolves device_id '1' -> user_id 12 (Juan) & logs telemetry
    API-->>ESP32: 200 OK {"status": "recorded", "choice": "B"}
    ESP32->>ESP32: Vote LED = SOLID GREEN (1.5s)
    API->>Screen: Update HDMI live grid: Clicker #1 turns GREEN [1: ✓]
    API->>Teacher: WebSocket/Polling: Clicker #1 [Juan] voted (Battery: 88%, Signal: Good)
```

---

## 5. Abstract `VoteTransport` Architecture (Week 3 & Week 7 Bridge)

To enforce **System Guardrail #5 (Hardware-Agnostic Transport)**, voting logic is completely decoupled behind an abstract `VoteTransport` interface:

```mermaid
classDiagram
    class VoteTransport {
        <<interface>>
        +record_vote(session_id: str, vote_data: dict) VoteResult
        +get_transport_name() str
    }

    class PwaWebTransport {
        +session_auth: SessionAuth
        +record_vote(session_id: str, vote_data: dict) VoteResult
    }

    class Esp32HardwareTransport {
        +device_registry: DeviceRegistry
        +record_vote(session_id: str, vote_data: dict) VoteResult
    }

    class QuizSessionEngine {
        -active_transports: list[VoteTransport]
        -votes_by_user: dict[int, str]
        +process_incoming_vote(user_id: int, choice: str)
        +compute_distribution() VoteDistribution
        +check_51_percent_threshold() DistractorIntervention
    }

    VoteTransport <|-- PwaWebTransport
    VoteTransport <|-- Esp32HardwareTransport
    QuizSessionEngine --> VoteTransport
```

---

## 6. Visual Feedback & Dual LED State Machines

The clicker incorporates two separate visual indicators: a **Primary RGB Vote LED** (front-facing for student quiz feedback) and a **Secondary Status LED** (for connection and power diagnostics).

### A. Primary RGB Vote LED (Quiz Feedback)
| State | LED Color / Pattern | Duration | Trigger Condition |
| :--- | :--- | :--- | :--- |
| **Idle / Standby** | `OFF` | Continuous | Waiting for student button press. |
| **Transmitting** | 🟡 **Blinking Yellow** (100ms) | Until HTTP response | Button pressed, transmitting packet. |
| **Vote Confirmed** | 🟢 **Solid Green** | 1.5 seconds | Server returned `200 OK` (`{"status": "recorded"}`). |
| **Error / Rejected** | 🔴 **Blinking Red** (3x 150ms) | ~1.0 second | Server returned `403` (unassigned), `409` (voting closed), or network timeout. |

### B. Secondary Status LED (Wi-Fi & Power Diagnostics)
| State | LED Color / Pattern | Duration | Condition |
| :--- | :--- | :--- | :--- |
| **Associating to Wi-Fi**| 🔵 **Fast Blinking Blue** | Boot until connected | Searching and associating to `TutorBox` AP. |
| **Wi-Fi Connected** | 🔵 **Solid Blue (3s then OFF)** | 3.0 seconds | DHCP lease acquired; device is online. |
| **Connection Failed** | 🔴 **Slow Blinking Red** | Continuous | Cannot associate with AP / wrong credentials. |
| **Low Battery Alert** | 🔴 **Pulsing Red** | Continuous | Battery voltage $< 3.3\text{V}$ ($< 15\%$). |
| **Charging (USB-C)** | 🟢 **Solid Green** (TP4056 LED) | While plugged in | Charging via 5V USB-C. |

---

## 7. Fleet Health Telemetry & Teacher PWA Dashboard

While the physical clicker has local LED warnings, **primary school students should not be responsible for diagnosing battery or network issues**.

Instead, TutorBox transmits real-time telemetry from every clicker directly to the **Teacher PWA Fleet Dashboard**:

### 1. In-Flight Telemetry Payload
Whenever a vote or 60-second periodic heartbeat is sent, the ESP32 includes hardware vitals:
```json
{
  "device_id": "1",
  "choice": "B",
  "battery_pct": 88,
  "voltage_mv": 3950,
  "rssi": -55
}
```

### 2. Teacher Fleet Health View (PWA UI)
In the Teacher Device Management view (`GET /devices`), the teacher sees a live status grid:

| Clicker # | Assigned Student | Status | Battery Level | Signal (RSSI) | Quick Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`#01`** | Juan Pérez | 🟢 Online | 🔋 88% | 📶 -55 dBm *(Good)* | `[Unpair]` |
| **`#02`** | María Gómez | 🟢 Online | 🔋 92% | 📶 -48 dBm *(Strong)* | `[Unpair]` |
| **`#03`** | Carlos Ruiz | 🟢 Online | 🪫 14% *(Low Alert)* | 📶 -62 dBm *(Moderate)* | `[Unpair]` |
| **`#04`** | *(Unassigned)* | ⚪ Standby | 🔋 100% | 📶 -50 dBm *(Strong)* | `[Pair Student]` |
| **`#05`** | Ana Morales | 🔴 Offline | ❓ Unknown | ❌ No Signal | `[Unpair]` |

* **Low-Battery Proactive Alerts**: If a clicker drops below $20\%$, the teacher sees a yellow warning icon and can swap the unit before starting a quiz.
* **Signal Quality (RSSI)**: Detects if a student is sitting in a Wi-Fi blind spot in the classroom.
* **Zero Student Confusion**: Students only interact with the simple 4 buttons and the green confirmation light.

---

## 8. Concurrency, Latency & Edge Case Resilience

### 1. Button Debounce & Lockout
* Clicker firmware enforces a **200ms hardware debounce** timer to eliminate contact bounce jitter.
* While transmitting or showing solid green, further button presses are ignored until the LED cycle completes.

### 2. In-Window Vote Overrides
* If the teacher's quiz timer is still running (e.g. 30-second window), a student who changes their mind can press a different button (e.g. 'C'). The backend updates `votes_by_user[user_id] = 'C'` and returns `200 OK`.

### 3. Unassigned Clicker Defense
* If an unassigned clicker sends a vote, the backend rejects with `403 Forbidden` (`{"detail": "Device is not assigned to any student."}`). The clicker blinks red 3 times to prompt the student to notify the teacher.

### 4. Router AP Capacity & Connection Budget
* The **GL-AR300M16 router** handles up to 30 simultaneous 802.11 b/g/n Wi-Fi stations on the 2.4GHz band.
* ESP32 firmware utilizes static IP assignment or cached DHCP leases to maintain connection latency under **150ms** per vote packet.

---

## 9. Implementation Roadmap & Milestones

```mermaid
gantt
    title Hardware Clicker & Voting Subsystem Timeline
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    section Week 1 (Completed)
    Database Migration 007 (devices table) :done, w1_1, 2026-08-23, 2026-08-30
    Staff Device REST Endpoints (/devices) :done, w1_2, 2026-08-23, 2026-08-30
    100% Quality Gate Verification         :done, w1_3, 2026-08-23, 2026-08-30
    section Week 3
    Abstract VoteTransport Interface       :active, w3_1, 2026-09-06, 2026-09-09
    Quiz Session Engine (>51% Rule)        :w3_2, 2026-09-09, 2026-09-13
    section Week 7
    ESP32 PlatformIO C++ Firmware          :w7_1, 2026-10-04, 2026-10-07
    Esp32HardwareTransport Driver          :w7_2, 2026-10-07, 2026-10-09
    Router AP Fleet Stress Test (15+ devs) :w7_3, 2026-10-09, 2026-10-11
```

---

## Next Steps

* **[REST API Reference](../api-reference.md)**: Explore the `/devices` and `/users` endpoint specifications.
* **[Database Schema Reference](../database-schema.md)**: Review table definitions and ER relationships.
* **[Hardware Topology](hardware-topology.md)**: Explore overall edge appliance hardware and RAM budgets.
