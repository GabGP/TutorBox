# System & Health API Specification

Technical specification for TutorBox health probes and core system diagnostics.

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../../infra/README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Docs](../README.md) › [REST API](README.md) › **System & Health** • **Related:** [Backend Guide](../../backend/README.md) • [Database Schema](../database/README.md)

</div>

---

## Endpoint Overview

The system and health probe endpoints allow the local Nginx reverse proxy, Docker containers, student PWAs, and monitoring daemons to check appliance liveness and SQLite database connectivity without requiring authentication.

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/health` | Public | System and database diagnostic probe |

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

## Related Specifications

* **[API Gateway & Policies](README.md)**: Global authentication flow, RBAC matrix, and standard error schemas.
* **[Authentication & Users](auth.md)**: User login, session tokens, and self-service registration.
* **[Hardware Topology](../architecture/hardware-topology.md)**: Appliance runtime constraints and memory allocation.
