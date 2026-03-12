# Full Data Flow (Phase 6.9)

End-to-end flow from sensors to cloud API and public/admin dashboards. Factory (offline) path runs without cloud; upload to cloud when online.

---

## Diagram

```
[Sensors: pH, TDS, Temp, Turbidity]
        ↓
[ESP32: read → 3x avg → threshold check → buzzer if alert]
        ↓
[Serial / WiFi]
        ↓
[Raspberry Pi / Local PC]
        ↓
[Sensor Fusion: filter → moving avg → baseline norm] → [Feature vector]
        ↓
[ML Inference: load model → predict sugar, citric, ascorbic → range check → Authentic/Adulterated]
        ↓
[Local Streamlit Dashboard: real-time graphs, alert box, state, mini log]
        ↓
[Cleaning automation: arm → rinse → dry → stabilise → READY]
        ↓
[HTTP POST] (when online)
        ↓
[Django API: /api/upload-data/] → [PostgreSQL: SensorReadings, Predictions, Alerts, SystemLogs]
        ↓
[React: Public dashboard (daily/weekly/monthly, graphs, badge, transparency)]
[React: Admin dashboard (raw data, alerts, logs)]
```

---

## Stages

| Stage | Component | Description |
|-------|-----------|-------------|
| 1 | Sensors | pH, TDS, temperature, turbidity (Phase 1 hardware). |
| 2 | ESP32 | Read sensors; 3× average; threshold check; buzzer on alert; output via Serial or WiFi. |
| 3 | Raspberry Pi / Local PC | Receives sensor stream. |
| 4 | Sensor Fusion | Filter → moving average → baseline norm → feature vector (Phase 2). |
| 5 | ML Inference | Load trained model; predict sugar, citric, ascorbic; range check → **Authentic** / **Adulterated** (Phase 3). |
| 6 | Local Streamlit | Real-time graphs, alert box, state, mini log (Phase 4). |
| 7 | Cleaning automation | Arm → rinse → dry → stabilise → READY (Phase 4, optional). |
| 8 | HTTP POST | When online: POST to Django `/api/upload-data/` with token auth. |
| 9 | Django + PostgreSQL | Persist SensorReadings, Predictions; create Alerts and SystemLogs when adulterated or out-of-range (Phase 5). |
| 10 | React | Public dashboard (daily/weekly/monthly aggregation, charts, authenticity badge, transparency); Admin dashboard (raw data, alerts, logs) (Phase 6). |

See **docs/DEPLOYMENT.md** for factory vs cloud placement and **phase.md** for phase breakdown.
