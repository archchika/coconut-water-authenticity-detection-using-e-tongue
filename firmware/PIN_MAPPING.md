# E-Tongue ESP32 — Pin Mapping & Configuration

**Phase 1.1 / 1.2** — Single source of truth: `include/config.h`. Sensor conversion coefficients in `config.h`; single-read logic in `src/sensors.cpp`.

## Pin mapping

| Function           | GPIO | Notes                          |
|--------------------|------|--------------------------------|
| pH sensor (ADC)    | 34   | Analog; 0–3.3 V                |
| TDS sensor (ADC)   | 35   | Analog; 0–3.3 V                |
| Temperature (ADC)  | 36   | NTC or analog temp output      |
| Turbidity (ADC)    | 39   | Analog; 0–3.3 V                |
| Buzzer             | 25   | Digital; active-high alert     |
| Rinse relay        | 26   | Distilled water pump control   |
| Dryer relay        | 27   | Dryer ON/OFF                   |
| Robot move (Phase 4.7) | 33 | Optional; pulse to trigger arm to cleaning station |

## ADC

- **Resolution:** 12-bit (0–4095).
- **Reference:** 3.3 V.
- **Formula (voltage):** `V = (raw / 4096.0f) * 3.3f`.

## Timing constants (config.h)

| Symbol                 | Default | Meaning                          |
|------------------------|---------|----------------------------------|
| `READ_DELAY_MS`        | 500     | Delay between each of 3 reads     |
| `NUM_READS`            | 3       | Readings per sensor for averaging|
| `SENSORS_REJECT_OUTLIERS` | 0    | 1 = median of 3; 0 = mean of 3     |
| `RINSE_DURATION_MS`    | 10000   | Rinse phase duration (ms)        |
| `DRYER_DURATION_MS`    | 30000   | Dryer phase duration (ms)        |
| `STABILIZE_READINGS`   | 5       | Phase 4.9: M consecutive pH in baseline to pass   |
| `STABILIZE_INTERVAL_MS`| 1000    | Phase 4.9: pH check interval (N seconds) during stabilize |
| `STABILIZE_TIMEOUT_MS` | 120000  | Max wait (2 min); then READY anyway|
| `USE_ROBOT_MOVE_STATION` | 1   | 0 = no-op; 1 = pulse robot pin (Phase 4.7) |
| `MOVE_TO_STATION_PULSE_MS` | 200  | Pulse length for robot trigger   |
| `MOVE_TO_STATION_WAIT_MS`  | 3000  | Wait for arm before rinse        |

## Folder structure

```
firmware/
├── platformio.ini
├── src/
│   ├── main.cpp
│   ├── sensors.cpp
│   ├── state_machine.cpp
│   ├── alerts.cpp
│   ├── transport.cpp
│   ├── cleaning.cpp
│   ├── stabilise.cpp
│   └── calibration.cpp
├── include/
│   ├── config.h
│   ├── sensors.h
│   ├── state_machine.h
│   ├── alerts.h
│   ├── transport.h
│   ├── cleaning.h
│   ├── stabilise.h
│   └── calibration.h
├── PIN_MAPPING.md
├── STATE_DIAGRAM.md
├── CALIBRATION_PROCEDURE.md
└── README.md
```

## Build and upload

```bash
cd firmware
pio run
pio run -t upload
pio device monitor
```

Requires [PlatformIO](https://platformio.org/) (CLI or VS Code extension).
