# ESP32 WiFi connection — Ceylon Coco / E-Tongue

Connect ESP32 to your factory WiFi and send sensor data to the Django backend.

---

## 1. Edit WiFi settings

Open **`firmware/include/config.h`** and set your network + PC IP:

```cpp
// ----- WiFi (for HTTP POST to Django backend) -----
#define WIFI_SSID          "maha"
#define WIFI_PASS          "12345678"
#define ML_SERVER_HOST     "10.234.124.31"      // PC IP (Django backend)
#define ML_SERVER_PORT     8000
#define ML_POST_PATH       "/api/esp32-reading/"
#define SOURCE_DEVICE_ID   "esp32-01"
```

Find PC IP on Windows:

```powershell
ipconfig
```

Use the **IPv4 Address** of the PC running Django. This project is configured for **`10.234.124.31`**. ESP32 and PC must be on the **same WiFi**.

---

## 2. WiFi connect code (already in project)

**`firmware/src/transport.cpp`** — connects and POSTs JSON:

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

void transport_wifi_connect(void) {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  // waits up to WIFI_CONNECT_TIMEOUT_MS (10 s)
}

bool transport_post_reading(const SensorReading_t* r, const char* status) {
  transport_wifi_connect();
  // POST http://ML_SERVER_HOST:8000/api/esp32-reading/
  // Body: {"timestamp_ms", "pH", "tds", "temperature", "turbidity", "status", "source_device_id"}
}
```

**`firmware/src/main.cpp`** — connects WiFi on boot:

```cpp
void setup() {
  Serial.begin(115200);
  // ... sensors, state machine ...
  transport_wifi_connect();
  transport_wifi_print_status();
}
```

---

## 3. Flash ESP32

```powershell
cd C:\Users\archchika\Desktop\research\firmware
pio run -t upload
pio device monitor -b 115200
```

Expected Serial output when WiFi works:

```
[WiFi] Connecting to "Your_WiFi_Name"...
........
[WiFi] Connected. IP: 192.168.1.42
[WiFi] Server: http://10.234.124.31:8000/api/esp32-reading/
[WiFi] OK | SSID=Your_WiFi_Name | IP=192.168.1.42 | RSSI=-55 dBm
```

---

## 4. Start Django on your PC (same network)

```powershell
cd C:\Users\archchika\Desktop\research\backend
.\run-lan.bat
```

Allow **Windows Firewall** inbound on port **8000**.

---

## 5. Serial commands

| Key | Action |
|-----|--------|
| **W** | Reconnect WiFi + print status |
| **G** | Start measurement cycle (reads sensors → POST × 3) |
| **C** | Enter calibration mode |

After **G**, each cycle sends **3 sensor snapshots** to `/api/esp32-reading/`.  
Backend runs **sensor fusion → ML → saves to database**.

Success on Serial:

```
[transport] POST OK HTTP 202 -> http://10.234.124.31:8000/api/esp32-reading/
[transport] POST OK HTTP 201 -> http://10.234.124.31:8000/api/esp32-reading/
```

---

## 6. JSON sent by ESP32

```json
{
  "timestamp_ms": 123456,
  "pH": 5.32,
  "tds": 4200.0,
  "temperature": 25.1,
  "turbidity": 28.0,
  "status": "unknown",
  "source_device_id": "esp32-01"
}
```

---

## 7. Troubleshooting

| Problem | Fix |
|---------|-----|
| `[WiFi] Failed` | Wrong SSID/password in `config.h` |
| `POST skipped: WiFi not connected` | Press **W** to reconnect; check router |
| `HTTP -1` or `http.begin failed` | Wrong `ML_SERVER_HOST`; PC firewall blocking 8000 |
| `HTTP 400` | Check JSON fields match backend |
| `HTTP 503` | Train ML: `python ML_1/train_model.py` and `python ML_2/train_model.py` |

---

## 8. Minimal WiFi-only test (Arduino IDE sketch)

If you only want to test WiFi + POST without full firmware, use this in a new `.ino` file:

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const char* WIFI_SSID = "Your_WiFi_Name";
const char* WIFI_PASS = "Your_WiFi_Password";
const char* SERVER    = "10.234.124.31";
const uint16_t PORT   = 8000;

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi OK: " + WiFi.localIP().toString());

  HTTPClient http;
  String url = String("http://") + SERVER + ":" + PORT + "/api/esp32-reading/";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  String body = "{\"pH\":5.5,\"tds\":3500,\"temperature\":25,\"turbidity\":20,\"source_device_id\":\"esp32-test\"}";
  int code = http.POST(body);
  Serial.printf("POST %s -> HTTP %d\n", url.c_str(), code);
  http.end();
}

void loop() {}
```

Run Django first, then upload this sketch. HTTP **202** or **201** = success.
