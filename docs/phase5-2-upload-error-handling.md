# Phase 5.2 — Upload error handling and retry

**Objective:** Retry with backoff on device/gateway, log failures locally, optional queue when offline.

---

## Firmware (ESP32)

- **Retries:** `TRANSPORT_POST_RETRIES` (default 3) in `firmware/include/config.h`.
- **Backoff:** Delay before each retry is **base × 2^attempt**: e.g. 1000 ms, 2000 ms, 4000 ms. Base = `TRANSPORT_POST_RETRY_DELAY_MS` (1000).
- **Logging:** Failures are printed to Serial:
  - `[transport] POST skipped: WiFi not connected` when WiFi is down.
  - `[transport] POST attempt N: http.begin failed` or `POST attempt N failed: HTTP <code>` on each failed attempt.
  - `[transport] POST failed after 3 retries (last HTTP <code>` when all retries are exhausted.

---

## Gateway (Python)

Use **`backend/upload_client.py`** on Raspberry Pi or any gateway that forwards readings to Django.

### `upload_reading(url, payload, ...)`

- **POST**s `payload` (dict) as JSON to `url` (e.g. `https://your-api.com/api/upload-data/`).
- **Retries** with exponential backoff on 5xx, connection errors, timeouts. Default: 3 attempts, backoff factor 2 (1s, 2s, 4s).
- **Logging:** Uses Python `logging`; warnings per failed attempt, error when all retries fail. Configure `logging` in your app to see output (e.g. `logging.basicConfig(level=logging.INFO)`).

Example:

```python
from backend.upload_client import upload_reading

payload = {
    "timestamp": "2025-02-25T10:30:00Z",
    "pH": 5.32,
    "tds": 420.5,
    "temperature": 26.1,
    "turbidity": 12.0,
    "status": "authentic",
}
if not upload_reading("https://api.example.com/api/upload-data/", payload):
    # Log or queue for later
    pass
```

### Optional queue when offline: `UploadQueue`

- **Push** payloads when upload fails; **flush** when connectivity is restored.
- Optional **max_size** to cap queue length (oldest dropped).

Example:

```python
from backend.upload_client import upload_reading, UploadQueue

queue = UploadQueue(max_size=50)
url = "https://api.example.com/api/upload-data/"

# After receiving a reading from ESP32 / ML:
if not upload_reading(url, payload):
    queue.enqueue_on_failure(payload)

# Periodically or when back online:
sent = queue.flush(url)
```

---

## Summary

| Location       | Retry              | Backoff        | Log failures     | Optional queue   |
|----------------|--------------------|----------------|------------------|------------------|
| ESP32 firmware | 3 attempts         | 1×, 2×, 4× base| Serial           | —                |
| Python gateway| 3 attempts (config)| Exponential    | logging module   | `UploadQueue`    |
