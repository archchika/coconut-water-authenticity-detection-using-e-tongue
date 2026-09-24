# Phone hotspot — ESP32 + PC setup

**Your PC IP on hotspot (detected): `10.234.124.31`**

Hotspot IP changes when you reconnect. Run `ipconfig` → Wi-Fi → IPv4 if POST fails.

---

## 1. Phone hotspot

1. Turn on **mobile hotspot** on your phone.
2. Connect **this PC** to the hotspot.
3. Connect **ESP32** to the **same** hotspot (SSID + password in firmware).

---

## 2. Edit `firmware/include/config.h`

```cpp
#define WIFI_SSID          "maha"
#define WIFI_PASS          "12345678"
#define ML_SERVER_HOST     "10.234.124.31"
```

---

## 3. Flash ESP32

```powershell
cd C:\Users\archchika\Desktop\research\firmware
pio run -t upload
pio device monitor -b 115200
```

Serial should show:
```
[WiFi] Connected. IP: ...
[WiFi] Server: http://10.234.124.31:8000/api/esp32-reading/
```

Press **W** to reconnect WiFi if needed.

---

## 4. Start backend (LAN)

Double-click **`backend\run-lan.bat`** or:

```powershell
cd C:\Users\archchika\Desktop\research\backend
.\run-lan.bat
```

Must show: `http://0.0.0.0:8000/`

---

## 5. Windows Firewall (once, as Administrator)

If ESP32 gets `HTTP -1`, allow port 8000:

```powershell
netsh advfirewall firewall add rule name="Django ESP32 8000" dir=in action=allow protocol=TCP localport=8000
```

---

## 6. Test from PC

```powershell
Invoke-RestMethod -Uri "http://10.234.124.31:8000/api/esp32-reading/" -Method POST -ContentType "application/json" -Body '{"pH":5.5,"tds":3500,"temperature":25,"turbidity":20,"source_device_id":"esp32-01"}'
```

Run **3 times** — 3rd response should have `"status": "complete"`.

---

## 7. ESP32 measurement

Serial: send **G** → look for:
```
[transport] POST OK HTTP 201 -> http://10.234.124.31:8000/api/esp32-reading/
```

Website: http://localhost:5173/admin → Sensor readings / Predictions (today, Apply).
