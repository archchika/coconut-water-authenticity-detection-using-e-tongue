# Phase 5.1 — IoT payload and endpoint design

**Objective:** Define the JSON structure for uploading E-Tongue readings from ESP32 or gateway to the cloud backend, and design the `POST /api/upload-data/` endpoint.

---

## Endpoint

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/upload-data/` |
| **Content-Type** | `application/json` |
| **Direction** | ESP32 or Raspberry Pi (gateway) → Django API |

---

## Request body (JSON payload)

### Required fields

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string or number | Time of the reading. **Preferred:** ISO 8601 UTC string (e.g. `"2025-02-25T10:30:00Z"`). **Accepted:** Unix milliseconds (number) — server will normalize to ISO. |
| `pH` | number | pH value (e.g. 4.5–7.0). |
| `tds` | number | TDS in ppm. |
| `temperature` | number | Temperature in °C. |
| `turbidity` | number | Turbidity (NTU or relative scale). |
| `status` | string | Result/health indicator. See allowed values below. |

### Optional fields (ML or gateway)

| Field | Type | Description |
|-------|------|-------------|
| `predicted_sugar` | number | ML-predicted sugar % (nullable if no ML). |
| `predicted_citric` | number | ML-predicted citric acid %. |
| `predicted_ascorbic` | number | ML-predicted ascorbic acid %. |
| `authenticity` | string | ML classification: `"Authentic"` or `"Adulterated"`. |
| `confidence` | number | ML confidence score in [0, 1] (optional). |
| `source_device_id` | string | Device or gateway identifier for traceability. |
| `system_state` | string | Firmware state at time of read (Phase 4.10): e.g. `IDLE`, `DETECTING`, `READ_COMPLETE`, `CLEANING`, `RINSING`, `DRYING`, `STABILIZE`, `READY`, `CALIBRATION`. |

### Allowed values for `status`

| Value | Meaning |
|-------|--------|
| `unknown` | No ML or threshold check yet. |
| `threshold_alert` | Sensor thresholds exceeded (firmware). |
| `authentic` | Within natural ranges / ML says authentic. |
| `adulterated` | ML or logic classifies as adulterated. |

---

## Example request

```json
{
  "timestamp": "2025-02-25T10:30:00Z",
  "pH": 5.32,
  "tds": 420.5,
  "temperature": 26.1,
  "turbidity": 12.0,
  "status": "authentic",
  "predicted_sugar": 2.1,
  "predicted_citric": 0.15,
  "predicted_ascorbic": 0.02,
  "authenticity": "Authentic",
  "source_device_id": "esp32-factory-01"
}
```

Minimal (sensor-only, no ML):

```json
{
  "timestamp": 1730010600000,
  "pH": 5.4,
  "tds": 400,
  "temperature": 25,
  "turbidity": 10,
  "status": "unknown"
}
```

---

## Response

### Success

| Status | Body |
|--------|------|
| `201 Created` | `{ "id": <reading_id>, "prediction_id": <id or null>, "created": "<ISO8601>" }` |

- `id`: Primary key of the stored sensor reading (and optionally the created prediction row).
- `prediction_id`: Set if ML fields were present and a Prediction record was created; else `null`.
- `created`: Server timestamp of the created record(s).

### Client error

| Status | Body |
|--------|------|
| `400 Bad Request` | `{ "error": "Validation error", "details": { "<field>": ["<message>", ...] } }` |

- Missing required field, invalid type, or invalid `status` value.

| Status | Body |
|--------|------|
| `401 Unauthorized` | `{ "error": "Authentication required" }` |

- When upload requires auth (Phase 5.7).

### Server error

| Status | Body |
|--------|------|
| `500 Internal Server Error` | `{ "error": "Internal server error" }` |

- Logged on server; client should retry with backoff (Phase 5.2).

---

## Mapping to database (reference for Phase 5.4–5.5)

- **SensorReadings:** `timestamp`, `pH`, `tds`, `temperature`, `turbidity`, `source_device_id`.
- **Predictions:** `reading_id` (FK), `timestamp`, `predicted_sugar`, `predicted_citric`, `predicted_ascorbic`, `authenticity_status` (from `authenticity` or `status`), `confidence`.
- **Alerts / SystemLogs:** Created on upload when `status` is `adulterated` or `threshold_alert` (Phase 5.8).

---

## Compatibility with existing systems

- **ESP32 (firmware):** Currently sends `timestamp_ms`, `pH`, `tds`, `temperature`, `turbidity`, `status`. Gateway or adapter should map `timestamp_ms` → `timestamp` (ISO or keep as number) and forward to this endpoint.
- **Sensor fusion / ML pipeline:** Can send the same shape as above with optional `predicted_*`, `authenticity`, `confidence`.
- **Local dashboard:** Reads from local ML server; cloud upload uses this payload when gateway POSTs to Django.
