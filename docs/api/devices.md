# Hardware Clicker & Device Fleet API Specification

Technical specification for physical ESP32 clicker registration, inventory management, and student pairing in **TutorBox**.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [REST API](README.md) › **Hardware Devices** • **Related:** [Staff Admin](staff.md) • [Clicker API](clicker.md) • [Clicker Firmware](../../firmware/clicker/README.md) • [Clicker Transport](../architecture/esp32-clicker-transport.md)

</div>

---

## Endpoint Overview

These endpoints govern the appliance's hardware inventory, allowing teachers and administrators to register physical 4-button ESP32 clickers and assign them to specific student accounts for classroom voting.

Since Week 7 a clicker registers itself: its first `POST /api/v1/clicker/checkin` adds it to this list, unassigned, with its secret's digest ([clicker.md](clicker.md)). The teacher only assigns it. `POST /staff/devices` is still useful to pre-register an id; the clicker claims that row on its first check-in.

From a laptop on the classroom Wi-Fi, [`tools/clickers/clickers.py`](../../tools/clickers/clickers.py) wraps these endpoints (`list`, `assign`, `assign-csv`, `unassign`, `forget`).

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/staff/devices` | Teacher, Admin | List all registered clickers and student assignments |
| `POST` | `/api/v1/staff/devices` | Teacher, Admin | Register a new clicker hardware ID into the fleet |
| `POST` | `/api/v1/staff/devices/{device_id}/assign` | Teacher, Admin | Pair a physical clicker to a student account |
| `POST` | `/api/v1/staff/devices/{device_id}/unassign` | Teacher, Admin | Unpair a physical clicker from any student |
| `DELETE` | `/api/v1/staff/devices/{device_id}` | Teacher, Admin | Remove a clicker identifier from the fleet |

---

## Detailed Contracts

### <a id="get-staff-devices"></a>`GET /api/v1/staff/devices`

List all registered physical clickers, their creation timestamps, current assigned student, and fleet health from their last check-in.

* **Authorization**: Teacher, Admin
* **Responses**:
  * `200 OK`:
    ```json
    {
      "devices": [
        {
          "device_id": "ESP32-A4CF12",
          "assigned_user_id": 12,
          "assigned_username": "juan_p",
          "created_at": "2026-08-29 14:00:00",
          "enrolled": true,
          "online": true,
          "last_seen_at": "2026-10-09 18:20:01",
          "rssi": -55,
          "battery_mv": 3950,
          "firmware": "1.0.0"
        },
        {
          "device_id": "ESP32_02",
          "assigned_user_id": null,
          "assigned_username": null,
          "created_at": "2026-08-29 14:05:00",
          "enrolled": false,
          "online": false,
          "last_seen_at": null,
          "rssi": null,
          "battery_mv": null,
          "firmware": null
        }
      ]
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.
* **Fleet health fields** (migration 012): `enrolled` is true once the clicker has checked in with its secret; `online` is true if it checked in within the last 45 s; `last_seen_at` (UTC), `rssi` (dBm), `battery_mv` and `firmware` come from that check-in, refreshed at most every 15 s.

---

### <a id="post-staff-devices"></a>`POST /api/v1/staff/devices`

Registers a new physical clicker identifier into the appliance fleet.

* **Authorization**: Teacher, Admin
* **Request Body**:
  ```json
  {
    "device_id": "1"
  }
  ```
* **Responses**:
  * `201 Created`:
    ```json
    {
      "device_id": "1",
      "assigned_user_id": null,
      "assigned_username": null,
      "created_at": "2026-08-29 14:00:00",
      "enrolled": false,
      "online": false,
      "last_seen_at": null,
      "rssi": null,
      "battery_mv": null,
      "firmware": null
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.
  * `409 Conflict`: `device_id` is already registered.
  * `422 Unprocessable Entity`: `device_id` is empty or invalid format.

---

### <a id="post-staff-devices-assign"></a>`POST /api/v1/staff/devices/{device_id}/assign`

Links a physical clicker to an active student user account.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `device_id` (`string`, required): Unique device identifier (e.g., `"1"`, `"ESP32_01"`).
* **Request Body**:
  ```json
  {
    "user_id": 12
  }
  ```
* **Responses**:
  * `200 OK`:
    ```json
    {
      "device_id": "1",
      "assigned_user_id": 12,
      "assigned_username": "juan_p"
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.
  * `404 Not Found`: Device or student account not found.
  * `422 Unprocessable Entity`: Target user account is not a student.

---

### <a id="post-staff-devices-unassign"></a>`POST /api/v1/staff/devices/{device_id}/unassign`

Unlinks a physical clicker from its currently paired student, setting `assigned_user_id = NULL`.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `device_id` (`string`, required): Unique device identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Device unassigned successfully."
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.
  * `404 Not Found`: Device not found.

---

### <a id="delete-staff-devices"></a>`DELETE /api/v1/staff/devices/{device_id}`

Removes a physical clicker identifier from the appliance database completely, together with its secret's digest. A clicker that is still powered on enrolls again, unassigned, on its next check-in: this is how a clicker whose flash was erased (new secret, `401` on check-in) is reset.

* **Authorization**: Teacher, Admin
* **Path Parameters**:
  * `device_id` (`string`, required): Unique device identifier.
* **Responses**:
  * `200 OK`:
    ```json
    {
      "detail": "Device removed from fleet."
    }
    ```
  * `403 Forbidden`: Caller is a student or has a pending PIN rotation.
  * `404 Not Found`: Device not found.

---

## Related Specifications

* **[ESP32 Clicker Transport Architecture](../architecture/esp32-clicker-transport.md)**: Hardware schematics, pairing flow, and LED state machines.
* **[Database Schema & ER Model](../database/README.md)**: `devices` table specifications and indexes.
* **[Quiz Match & Voting Sessions](sessions.md)**: How device votes are mapped to student IDs.
