# System & Health API Specification

Technical specification for TutorBox health probes, captive-portal connectivity probes, and core system diagnostics.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
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
  "service": "TutorBox Backend",
  "database": "healthy"
}
```

#### Response Fields
| Field | Type | Description |
| :--- | :--- | :--- |
| `status` | string | Overall service health (`"ok"`). |
| `service` | string | Human-readable service banner (`"TutorBox Backend"`). |
| `database` | string | Database engine connection status (`"healthy"`). |

---

### <a id="captive-portal-probes"></a>Captive-portal probes (`GET /generate_204`, `GET /hotspot-detect.html`, …)

Answered by `backend/src/api/captive.py` for **any** `Host` header. Hidden from `/openapi.json`.

* **Authorization**: Public
* **Rate Limiting**: Exempt
* **Configuration**: `CAPTIVE_PORTAL_ENABLED` (default `true`), `CAPTIVE_PORTAL_URL` (default `http://tutorbox/alumno/`)

#### Response (`302 Found`)
```http
HTTP/1.1 302 Found
Location: http://tutorbox/alumno/
Cache-Control: no-store
```

With `CAPTIVE_PORTAL_ENABLED=false` the probes answer `404 {"detail": "Not Found"}`.

The same `302` is returned for `GET`/`HEAD` of any unknown page — and of `/` — when the request's `Host` is not the appliance itself (`localhost`, an IP literal, or the hostname of `CAPTIVE_PORTAL_URL`). Paths under `/api/`, `/health`, `/maestro/`, `/alumno/`, `/pantalla/` and `/static/` are exempt and keep their normal 404s, so hardware clickers never see a redirect. Full flow, router prerequisites and limitations: [Captive Portal](../../infra/captive-portal.md).

---

## Related Specifications

* **[API Gateway & Policies](README.md)**: Global authentication flow, RBAC matrix, and standard error schemas.
* **[Authentication & Users](auth.md)**: User login, session tokens, and self-service registration.
* **[Hardware Topology](../architecture/hardware-topology.md)**: Appliance runtime constraints and memory allocation.
* **[Captive Portal](../../infra/captive-portal.md)**: How the probes above open the student page on Wi-Fi join.
