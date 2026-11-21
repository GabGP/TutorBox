# System & Health API Specification

Technical specification for Utz'tutor health probes, captive-portal connectivity probes, and core system diagnostics.

<div align="center">

| 🏠 [Utz'tutor](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [REST API](README.md) › **System & Health** • **Related:** [Backend Guide](../../backend/README.md) • [Database Schema](../database/README.md) • [Captive Portal](../../infra/captive-portal.md)

</div>

---

## Endpoint Overview

The system and health probe endpoints allow the local nginx reverse proxy, student PWAs, and monitoring daemons to check appliance liveness and SQLite database connectivity without requiring authentication. The captive-portal probes are the URLs phones fetch right after joining the Wi-Fi; answering them with a redirect is what opens the student page automatically.

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/health` | Public | System and database diagnostic probe |
| `GET`/`HEAD` | `/generate_204`, `/gen_204`, `/hotspot-detect.html`, `/library/test/success.html`, `/connecttest.txt`, `/ncsi.txt`, `/redirect`, `/success.txt`, `/canonical.html`, `/check_network_status.txt` | Public | Captive-portal connectivity probes → `302` to the student page |
| `GET` | `/api/v1/mode` | Public | Classroom-wide active mode (`quiz`, `tutor`, `apps`) |
| `PUT` | `/api/v1/mode` | Teacher, Admin | Teacher switches the active mode from their phone; the answer says what happened to the tutor model |

---

## Detailed Contract

### <a id="get-health"></a>`GET /health`

Checks the availability of the FastAPI service process and verifies that the local SQLite database connection pool and WAL journal are responsive.

* **Authorization**: Public (No credentials required)
* **Rate Limiting**: Exempt
* **Query Parameters**: None
* **Request Headers**: None

#### Success Response (`200 OK`)
```json
{
  "status": "ok",
  "service": "Utz'tutor Backend",
  "database": "healthy"
}
```

#### Response Fields
| Field | Type | Description |
| :--- | :--- | :--- |
| `status` | string | Overall service health (`"ok"`). |
| `service` | string | Human-readable service banner (`"Utz'tutor Backend"`). |
| `database` | string | Database engine connection status (`"healthy"`). |

---

### <a id="captive-portal-probes"></a>Captive-portal probes (`GET /generate_204`, `GET /hotspot-detect.html`, …)

Answered by `backend/src/api/captive.py` for **any** `Host` header. Hidden from `/openapi.json`.

* **Authorization**: Public
* **Rate Limiting**: Exempt
* **Configuration**: `CAPTIVE_PORTAL_ENABLED` (default `true`), `CAPTIVE_PORTAL_URL` (default `http://utztutor/alumno/`)

#### Response (`302 Found`)
```http
HTTP/1.1 302 Found
Location: http://utztutor/alumno/
Cache-Control: no-store
```

With `CAPTIVE_PORTAL_ENABLED=false` the probes answer `404 {"detail": "Not Found"}`.

The same `302` is returned for `GET`/`HEAD` of any unknown page — and of `/` — when the request's `Host` is not the appliance itself (`localhost`, an IP literal, or the hostname of `CAPTIVE_PORTAL_URL`). Paths under `/api/`, `/health`, `/maestro/`, `/alumno/`, `/pantalla/`, `/static/`, `/tareas/` and `/descargas/` are exempt and keep their normal 404s, so hardware clickers never see a redirect. Full flow, router prerequisites and limitations: [Captive Portal](../../infra/captive-portal.md).

---

### <a id="classroom-mode"></a>Classroom mode (`GET` / `PUT /api/v1/mode`)

The appliance has a screen but no keyboard, so the teacher picks the active mode from `/maestro/`
on their phone. The classroom screen (`/pantalla/`) and student phones (`/alumno/`) poll `GET` and
follow the choice. Implemented in `backend/src/api/mode.py`, stored in the single-row
`appliance_state` table ([core.md](../database/core.md#table-appliance_state)), so it survives a reboot.

| Mode | Meaning |
| :--- | :--- |
| `quiz` | Kahoot-style classroom quiz (default). |
| `tutor` | Socratic tutor chat (Week 5). |
| `apps` | Students download the take-home Android app from [`/descargas/`](../../pwa/README.md#3-tareas--take-home-math-apps-tareas). |

* **`GET`** — Public, no body. `200 {"mode": "quiz"}`.
* **`PUT`** — `require_roles("teacher", "admin")`. Body `{"mode": "tutor"}` → `200`:
  ```json
  {"mode": "tutor", "model": {"model": "hf.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q8_0",
   "action": "loaded", "duration_ms": 3200.0, "detail": null, "gpu_percent": 100}}
  ```
  `model` is the tutor model's outcome (see [Model residency](#model-residency)); it is always present.
  The answer waits for the load, so a switch into tutor mode takes as long as the load does. Records a `mode_changed` audit event. Two switches that arrive together are
  applied one after the other, so the last one decides both the saved mode and the model.

| Status | Trigger |
| :--- | :--- |
| `401` | Missing or invalid bearer token. |
| `403` | Caller is a student, or has a pending PIN rotation. |
| `409` | Switching away from `quiz` while a session is `active`: `{"detail": "Termina el juego antes de cambiar de modo."}`. A session still in `lobby` does not block. |
| `422` | `mode` is not one of `quiz`, `tutor`, `apps`. |

### <a id="model-residency"></a>Model residency (the Ollama models in memory)

The appliance serves two models through Ollama (`SLM_BASE_URL`): the quiz model (`SLM_MODEL_NAME`,
`qwen2.5:3b`) and the tutor model (`TUTOR_MODEL_NAME`, a DeepSeek-R1 distill of 1.5B parameters). Both
together take a large part of the Jetson's 8 GB shared with the voice engine, so the backend keeps each
one in memory only while the classroom needs it. Implemented in `backend/src/core/llm/residency/`.

* **Tutor model**: loaded when the class enters `tutor` mode (the `PUT` above waits for the load), and
  unloaded when the class leaves it.
* **Quiz model**: loaded when a teacher's question batch starts (`POST /api/v1/quiz/model/load`) and
  unloaded when the batch ends, is cancelled or is abandoned (`POST /api/v1/quiz/model/unload`). A
  generation that finds the model unloaded loads it itself. If no generation runs for
  `SLM_QUIZ_IDLE_UNLOAD_SECONDS` (default 90), the backend unloads the model anyway: that covers a
  teacher who closed the page in the middle of a batch.
* **Ollama keeps models until told otherwise.** Its OpenAI endpoint ignores `keep_alive`, and its
  default is 5 minutes, which would evict the tutor model in a quiet tutor session. The Ansible setup
  installs the drop-in [`infra/systemd/ollama-utztutor.conf`](../../infra/systemd/ollama-utztutor.conf)
  (`OLLAMA_KEEP_ALIVE=-1`, `OLLAMA_MAX_LOADED_MODELS=2`), so the backend alone decides when a model leaves.
* **At startup** the backend unloads a quiz model left in memory by an earlier run, then applies the saved
  mode. It runs in a background thread, so startup never waits for Ollama.

The `model` outcome (in the `PUT` above and in the two quiz endpoints) has these values for `action`:

| `action` | Meaning |
| :--- | :--- |
| `loaded` | The model is in memory. `duration_ms` is the load time; `gpu_percent` is the share Ollama placed on the GPU (from `/api/ps`: `size_vram / size`), or `null` when it does not say. |
| `unloaded` | The model was dropped from memory. |
| `kept` | Left in memory because the other role still needs it: the quiz and tutor models are one and the same, and a quiz batch or tutor mode still uses it. |
| `failed` | Ollama refused the request or did not answer; `detail` says why. Nothing else fails: the mode is saved and a generation still runs. |
| `unsupported` | The server at `SLM_BASE_URL` has no Ollama model API (for example llama.cpp). Nothing is managed. |
| `disabled` | `SLM_MANAGE_RESIDENCY=false`: the backend never calls Ollama's model API. |

`detail` is for logs. The teacher's screen shows only a toast for `loaded`, `unloaded` and `failed`.

`gpu_percent` below 100 means the Jetson had too little free memory when the model loaded: Ollama ran
the remaining layers on the CPU, several times slower (on 2026-11-21 the quiz model got 24 of its 37
layers on the GPU and one attempt passed the 120 s timeout, against 18–30 s with all 37). The backend
logs a warning, and the teacher's screen shows a warning toast in place of the success toast. The
`gpu_percent` field is only set for `loaded`.

---

## Related Specifications

* **[API Gateway & Policies](README.md)**: Global authentication flow, RBAC matrix, and standard error schemas.
* **[Authentication & Users](auth.md)**: User login, session tokens, and self-service registration.
* **[Hardware Topology](../architecture/hardware-topology.md)**: Appliance runtime constraints and memory allocation.
* **[Captive Portal](../../infra/captive-portal.md)**: How the probes above open the student page on Wi-Fi join.
