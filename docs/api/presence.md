# Presence API: Connection Heartbeat & Class View

Technical specification for the heartbeat that tells the appliance a phone or a clicker is still connected, and for the teacher's class view that shows it before a match starts.

<div align="center">

| 🏠 [Utz'tutor](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [REST API](README.md) › **Presence** • **Related:** [Hardware Devices](devices.md) • [Quiz Match & Voting](sessions.md) • [Clicker Transport](../architecture/esp32-clicker-transport.md)

</div>

---

Phones and ESP32 clickers do not hold a connection to the appliance, and the poll they wait on (`GET /api/v1/session/current`) is public, so it does not say who is connected. Each client sends a heartbeat instead, and the teacher's lobby reads the class view. Code: `backend/src/api/presence/` (HTTP, status rules and the in-memory store) and `backend/src/core/db/class_roster_repository.py` (the students and clickers of the class).

## Endpoint Overview

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/presence/heartbeat` | Any live session | Says that the phone or clicker is still there. Answers `204` with no body. |
| `GET` | `/api/v1/presence/class` | Teacher, Admin | The class with the connection status of each student's phone and clicker. |

## Thresholds

| Rule | Value |
| :--- | :--- |
| Beat expected from a client | Every 5 seconds |
| `online` | Last beat 15 seconds ago or less |
| `dropped` | Last beat more than 15 seconds ago, and less than 30 minutes |
| `absent` | Never heard from, or not heard from for 30 minutes (the entry is then forgotten) |
| Signal `good` | RSSI of -65 dBm or better |
| Signal `fair` | RSSI from -66 to -75 dBm |
| Signal `weak` | RSSI below -75 dBm |

The values are constants in `backend/src/api/presence/status.py` (`ONLINE_SECONDS`, the signal levels) and `backend/src/api/presence/store.py` (`FORGET_SECONDS`).

---

## <a id="post-presence-heartbeat"></a>`POST /api/v1/presence/heartbeat`

Records that the caller is connected. The caller's session decides what is recorded:

| Caller | Recorded | Body |
| :--- | :--- | :--- |
| Clicker (its token, see [Devices API](devices.md#post-devices-auth)) | The clicker, under its `device_id`, with the vitals sent | `rssi` and `battery_pct` are read |
| Student login (phone or browser) | The phone of that student | Any vitals are ignored |
| Teacher or admin login | Nothing | Ignored |

* **Authorization**: any live session. The endpoint takes the same tokens as the vote endpoint (`get_voter_session`): a student's login, a clicker's token, or a staff login. A pending PIN rotation is not checked, as on the vote endpoint.
* **Request Body**: optional. A request with no body is accepted, which is what phones send.
  ```json
  {
    "rssi": -58,
    "battery_pct": 88
  }
  ```
  * `rssi` (`integer`, optional): the clicker's Wi-Fi signal in dBm, from -120 to 0. `null` or absent when unknown.
  * `battery_pct` (`integer`, optional): the clicker's battery in percent, from 0 to 100. `null` or absent when unknown.
  * Other fields are ignored.
* **Responses**:
  * `204 No Content`: the beat is recorded, or the caller is a staff login and nothing is recorded.
  * `401 Unauthorized`: `"Missing or malformed Authorization header."` with no bearer token; `"Invalid session token."` when the token is not a UUID; `"Invalid or expired session."` for an unknown, revoked or expired token. A clicker whose token was revoked gets `401` and authenticates again (see [Clicker Token Revocation](devices.md#clicker-token-revocation)).
  * `422 Unprocessable Content`: `rssi` outside -120 to 0, or `battery_pct` outside 0 to 100.
* **Notes**:
  * Only the heartbeat refreshes the presence. Votes, tutor messages and other requests do not.
  * A clicker's vitals are stored with the beat that carried them. A beat without them clears the previous values.
  * The server never writes the token to a log or an error message.

---

## <a id="get-presence-class"></a>`GET /api/v1/presence/class`

The class as the teacher's lobby lists it: every student, with the status of their phone and of their clicker, and the clickers that have no student.

* **Authorization**: Teacher, Admin
* **Responses**:
  * `200 OK`:
    ```json
    {
      "online": 18,
      "total": 24,
      "students": [
        {
          "user_id": 7,
          "username": "ana",
          "status": "online",
          "phone": {"status": "absent", "seconds_ago": null},
          "clicker": {
            "device_id": "ESP32-A4CF12", "status": "online", "seconds_ago": 3,
            "signal": "good", "rssi": -58, "battery_pct": 88
          }
        }
      ],
      "unassigned_clickers": ["ESP32-B7C001"]
    }
    ```
  * `401 Unauthorized`: as for the heartbeat.
  * `403 Forbidden`: `"Insufficient permissions."` for a student; `"Clicker sessions can only vote."` for a clicker's token; `"PIN change required."` while a PIN rotation is pending.
* **Fields**:
  * `online`: the number of students whose `status` is `online`.
  * `total`: the number of students listed.
  * `students`: every active student account (`role` `student`, not deleted), ordered by username. A student who never connected is listed as `absent`.
  * `status` (student): the better of the phone's status and the clicker's status: `online` beats `dropped`, which beats `absent`.
  * `phone`: always present. `status` is `online`, `dropped` or `absent`, and `seconds_ago` is `null` when `absent`.
  * `clicker`: `null` when the student has no clicker assigned. A clicker that was assigned but never seen has `status` `absent` and `signal`, `rssi` and `battery_pct` all `null`. A clicker that stopped keeps the last vitals it sent, with `status` `dropped`.
  * `signal`: `good`, `fair`, `weak`, or `null` when no RSSI is known.
  * `unassigned_clickers`: the ids of the registered clickers that no listed student has. That is a clicker with no student, or one whose student's account is deleted or is no longer a student. Ordered by id. Such a clicker has no token, so it cannot send a heartbeat and has no vitals here.
* **Notes**:
  * The assignment allows one clicker per student, so a student has at most one. If two ever pointed at one student, the student would be listed once, with the lowest `device_id`, and the other clicker would appear in `unassigned_clickers`.

---

## Storage and Restart

The presence state lives in memory, in the one process that serves the API (the systemd unit runs uvicorn without `--workers`). A restart empties it. Each phone and clicker beats every 5 seconds, so the lobby is complete again within seconds of a restart. Nothing about presence is written to the database.

An entry that has not beaten for 30 minutes is forgotten: it is removed on the next lookup or write, so the memory stays bounded by the size of the class.

## Related Specifications

* **[Hardware Devices API](devices.md)**: The clicker secret, the clicker login and the clicker token.
* **[Quiz Match & Voting](sessions.md)**: The vote, which a clicker's token also uses.
* **[ESP32 Clicker Transport](../architecture/esp32-clicker-transport.md)**: The clicker's vitals and the lobby's use of them.
