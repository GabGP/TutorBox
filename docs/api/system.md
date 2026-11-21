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
| `GET` | `/api/v1/system/health` | Teacher, Admin | Jetson health panel: CPU, GPU, memory, temperatures, power, disk, models and voices in memory |
| `POST` | `/api/v1/system/free-memory` | Teacher, Admin | Frees the models and voices the current mode does not need, loads back what it needs, and reports the RAM before and after |

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

### <a id="jetson-health"></a>Jetson health (`GET /api/v1/system/health`)

The teacher's **Estado del Jetson** sheet (`pwa/app/src/features/system-health/`) reads this endpoint every 5 seconds while the sheet is open and the page is visible, and stops when the sheet closes. The readers live in `backend/src/core/system_health/` and the route in `backend/src/api/system/health.py`.

* **Authorization**: Teacher, Admin. `401` without a session; `403` for a student or a clicker.
* **Cache**: one sample is kept for 2 seconds (monotonic clock, one lock), so several open panels share one set of reads. The first sample takes about 0.2 s, because it needs two readings of the CPU counters; later samples measure the time since the previous one.
* **Unreadable metrics are `null` (or an empty list), never an error.** A PC or the CI machine, where these files differ or are absent, still answers `200`.
* **Reads are files, not processes**: no `tegrastats` is started, and no `sudo` is needed.

#### Success Response (`200 OK`)
```json
{
  "sampled_at": "2026-11-21T06:30:00+00:00",
  "cpu": {
    "usage_percent": 35.9,
    "per_core": [{"index": 0, "usage_percent": 35.0, "freq_mhz": 1190}],
    "status": "ok"
  },
  "memory": {"total_mb": 7485.4, "available_mb": 3385.7, "used_percent": 54.8, "swap_total_mb": 0.0, "swap_used_mb": 0.0, "status": "ok"},
  "gpu": {"load_percent": 99.8, "freq_mhz": 306, "max_freq_mhz": 918, "status": "ok"},
  "temperatures": [{"zone": "gpu-thermal", "celsius": 62.4, "status": "ok"}],
  "power": [{"rail": "VDD_IN", "milliwatts": 5981}],
  "disk": {"total_gb": 914.3, "free_gb": 821.0, "free_percent": 89.8, "status": "ok"},
  "uptime_seconds": 98992.6,
  "load_average": [3.32, 4.45, 3.74],
  "models": [{"name": "qwen2.5:3b", "gpu_percent": 100}],
  "voices": ["piper"]
}
```

#### Response Fields
| Field | Type | Description |
| :--- | :--- | :--- |
| `sampled_at` | string | UTC time of the sample (ISO 8601). The panel shows its age. |
| `cpu.usage_percent` | number or null | Busy share of all cores since the previous sample. |
| `cpu.per_core[]` | array | One entry per core: `index` (from 0), `usage_percent`, `freq_mhz` (current clock). |
| `memory` | object or null | RAM shared by the CPU and the GPU: `total_mb`, `available_mb` (what the models and the voice can still use), `used_percent`, and the swap in MB. |
| `gpu` | object or null | `load_percent`, current and maximum clock (`freq_mhz`, `max_freq_mhz`). |
| `temperatures[]` | array | One entry per thermal zone: `zone` (its type, such as `cpu-thermal`), `celsius`. Zones that read nothing or an impossible value (outside −40 to 150 °C) are left out. |
| `power[]` | array | Each labelled `VDD_*` rail of the INA3221 monitor: `rail`, `milliwatts`. `VDD_IN` is the whole board. |
| `disk` | object or null | Size and free space of the partition that holds the database (`total_gb`, `free_gb`, `free_percent`). |
| `uptime_seconds`, `load_average` | number or null, array or null | Seconds since boot; the 1, 5 and 15 minute load averages. |
| `models[]` | array | Ollama models in memory: `name`, `gpu_percent` (share on the GPU, `null` when Ollama does not say). |
| `voices[]` | array | Canonical names of the voice engines with weights in memory. `espeak` is never listed: it runs a small process per sentence and keeps nothing loaded, although the TTS router reports it as loaded whenever it is installed. |
| `*.status` | string | `ok`, `warn`, `critical` or `unknown` (the reading is missing). Power, models and voices have no status. |

#### Where each reading comes from (on the Jetson)
| Reading | Source |
| :--- | :--- |
| CPU usage and per-core clock | `/proc/stat` (two samples); `/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq` |
| Memory and swap | `/proc/meminfo` (`MemTotal`, `MemAvailable`, `SwapTotal`, `SwapFree`) |
| GPU load and clocks | `/sys/devices/platform/bus@0/*.gpu/load` (per mille); `/sys/class/devfreq/*.gpu/cur_freq` and `max_freq` (Hz) |
| Temperatures | `/sys/devices/virtual/thermal/thermal_zone*/type` and `temp` (millidegrees) |
| Power | `/sys/bus/i2c/drivers/ina3221/*/hwmon/hwmon*`: `in{N}_label`, `in{N}_input` (mV) and `curr{N}_input` (mA) |
| Disk | `shutil.disk_usage` on the folder of `DATABASE_PATH` |
| Uptime and load | `/proc/uptime`, `/proc/loadavg` |
| Models in memory | Ollama `/api/ps` through `OllamaResidencyClient`, only when `SLM_MANAGE_RESIDENCY` is true, with a 2-second timeout so a hung Ollama cannot stall the panel. A failed answer gives `models: []`, never an error. |
| Voices | `TTSRouter.loaded_engines()` |

The power mode (`nvpmodel`) is not reported.

#### Status thresholds
The limits are named constants in `backend/src/core/system_health/thresholds.py`; this table is the same list.

| Reading | `warn` | `critical` | Why |
| :--- | :--- | :--- | :--- |
| Temperature (hottest zone) | ≥ 80 °C | ≥ 95 °C | The Orin Nano throttles its clocks near 99 °C and shuts down near 104 °C. |
| Memory available | < 1.5 GB | < 0.75 GB | The quiz model needs about 2.4 GB to sit entirely on the GPU. |
| CPU usage | ≥ 85 % | none | Sustained load leaves too little CPU for the voice and the web server. |
| GPU load | none | none | Informational: the GPU is busy during every generation, which is normal. |
| Disk free space | < 10 % | < 5 % | The database and the logs grow with every class. |

`GET /health` stays the public watchdog check. nginx, the watchdog and `verify.yml` use it, and its answer and status codes are unchanged; this staff endpoint does not replace it.

### <a id="free-memory"></a>Memory release (`POST /api/v1/system/free-memory`)

The **Liberar memoria** button in the Estado del Jetson sheet calls this endpoint. It frees what the current classroom mode does not need, and loads back only what the mode asks for. Implemented in `backend/src/core/system_health/` (`memory_release.py`, `model_release.py`, `voice_release.py`, `heap.py`) and `backend/src/api/system/free_memory.py`.

* **Authorization**: Teacher, Admin. `401` without a session; `403` for a student.
* **Never raises**: every step is guarded. A refused, unreachable or slow Ollama, or a failing voice, is reported as an action with `"action": "failed"` and the response is still `200`.
* **Steps, in order**:
  1. Reads the available RAM (`MemAvailable`).
  2. **Quiz model**: unloaded through `release_quiz()`, unless a question generation is running; then it is `kept`.
  3. **Tutor model**: `apply_mode(saved mode)`. Outside tutor mode it is unloaded; in tutor mode it is loaded again (the same model as the quiz is `kept`).
  4. **Voices**: every loaded engine is unloaded (`unload(engine=...)`), unless the newest quiz session is `active` (a game is running); then each is `kept`. The speech endpoint loads a voice again when it is needed.
  5. **Backend heap**: `gc.collect()`, then `malloc_trim(0)` through glibc on Linux, which returns the freed heap pages to the system. Other systems report `unsupported`.
  6. Waits one second, reads the RAM again, and drops the cached health sample, so the next panel read is fresh.
* With `SLM_MANAGE_RESIDENCY=false`, the two models are `disabled` and Ollama is not called.
* **Only what was in memory is reported**: the release asks Ollama which models are resident (`GET /api/ps`, 2 s timeout) and leaves a model that is not loaded out of `actions`, so the toast never says something was unloaded when nothing was. In tutor mode the tutor model is still loaded and reported as `loaded`. When Ollama cannot say, every step is reported (unloading a model that is not loaded is harmless). `espeak` is skipped for the same reason as in `voices[]`.

#### Success Response (`200 OK`)
```json
{
  "available_before_mb": 1000.0,
  "available_after_mb": 3355.2,
  "freed_mb": 2355.2,
  "actions": [
    {"target": "qwen2.5:3b", "kind": "quiz_model", "action": "unloaded", "detail": null},
    {"target": "voz qwen3-tts", "kind": "voice", "action": "unloaded", "detail": null},
    {"target": "hf.co/bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF:Q8_0", "kind": "tutor_model", "action": "loaded", "detail": null},
    {"target": "heap del proceso", "kind": "backend_heap", "action": "unloaded", "detail": "malloc_trim returned free pages"}
  ]
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `available_before_mb`, `available_after_mb` | number or null | RAM available before and after the release (MB). `null` when unreadable. |
| `freed_mb` | number or null | After minus before. It can be negative when other programs used RAM meanwhile. |
| `actions[]` | array | One entry per step: `target` (model name, `voz <engine>`, `voces`, or `heap del proceso`), `kind` (`quiz_model`, `tutor_model`, `voice`, `backend_heap`), `action`, and `detail` (for logs). |

| `action` | Meaning |
| :--- | :--- |
| `unloaded` | Dropped from memory now. For the heap, the trim ran. |
| `loaded` | The tutor model is in memory again (tutor mode). |
| `kept` | Left in memory: a question generation runs, a quiz game is active, or the quiz and tutor are the same model. |
| `failed` | The step could not be done (Ollama down, a voice that would not unload, an unreadable saved mode). Nothing else is affected. |
| `disabled` | `SLM_MANAGE_RESIDENCY=false`: Ollama was not called. |
| `unsupported` | The server has no Ollama model API, or the platform has no glibc `malloc_trim`. |

---

## Related Specifications

* **[API Gateway & Policies](README.md)**: Global authentication flow, RBAC matrix, and standard error schemas.
* **[Authentication & Users](auth.md)**: User login, session tokens, and self-service registration.
* **[Hardware Topology](../architecture/hardware-topology.md)**: Appliance runtime constraints and memory allocation.
* **[Captive Portal](../../infra/captive-portal.md)**: How the probes above open the student page on Wi-Fi join.
