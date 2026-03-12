# E-Tongue ESP32 Firmware

Phase 1 — Foundation & Hardware Layer. **Phase 1.10:** Integration, testing, and documentation complete.

## Integration summary

All modules are wired in **setup()** and **loop()**:

| Module        | Init (setup)           | Used in loop / state machine        |
|---------------|------------------------|-------------------------------------|
| Sensors       | `sensors_load_calibration()` | DETECTING, STABILIZE, calibration   |
| Alerts        | `alerts_init()`        | Threshold check, buzzer on/off      |
| Cleaning      | `cleaning_init()`      | RINSING, DRYING relay control        |
| State machine | `state_machine_init()` | `state_machine_tick()` every loop   |
| Transport     | `transport_wifi_connect()` | READ_COMPLETE: Serial log, HTTP POST |
| Stabilise     | (reset in init)        | STABILIZE: pH baseline check        |
| Calibration   | —                      | Serial `C` / `S` / `Q` in IDLE or CALIBRATION |

Serial commands: **G** = start cycle (from IDLE); **C** = enter calibration; **S** = sample and save; **Q** = quit calibration.

## Prerequisites

- [PlatformIO](https://platformio.org/) (VS Code extension or CLI: `pip install platformio`).

## Build

```bash
cd firmware
pio run
```

## Upload

Connect ESP32 via USB, then:

```bash
pio run -t upload
```

## Monitor (Serial)

```bash
pio device monitor -b 115200
```

## Configuration

- **Pin mapping, ADC, timing, thresholds:** `include/config.h`
- **Pin table and folder layout:** `PIN_MAPPING.md`

Edit `config.h` to match your wiring and WiFi (e.g. `WIFI_SSID`, `WIFI_PASS`, `ML_SERVER_HOST`).

**State machine (1.4):** In IDLE, send `G` on Serial to start a cycle, or wait 5 s for auto-start. Cycle: DETECTING → READ_COMPLETE → CLEANING → RINSING → DRYING → STABILIZE → READY → IDLE.

**Calibration (1.9):** In IDLE, send `C` to enter calibration mode. Place probe in known solution (e.g. pH 7 buffer; see `config.h` CAL_KNOWN_*). Send `S` to sample and save offsets to NVS; send `Q` to quit without saving.

## Documentation

- **PIN_MAPPING.md** — Pin table, ADC, timing constants, folder layout.
- **STATE_DIAGRAM.md** — State machine diagram and transition table.
- **CALIBRATION_PROCEDURE.md** — Step-by-step operator calibration.

## Verification and testing

1. **Build and upload** — `pio run` then `pio run -t upload`; open monitor at 115200.
2. **Boot** — Expect `E-Tongue ESP32 — Phase 1.9 calibration ready` and state `IDLE`.
3. **Start cycle** — Send `G` (or wait 5 s auto-start). Expect states in order: DETECTING → READ_COMPLETE → CLEANING → RINSING → DRYING → STABILIZE → READY → IDLE. On READ_COMPLETE, one JSON line on Serial and (if WiFi configured) HTTP POST to ML server.
4. **Threshold alert** — If any sensor is out of safe range (config.h), buzzer turns on until CLEANING.
5. **Relays** — In RINSING, rinse relay (PIN_RINSE_RELAY) HIGH for 10 s; then dryer relay (PIN_DRYER_RELAY) HIGH for 30 s; both OFF in STABILIZE.
6. **Calibration** — Send `C`; place probe in reference; send `S`. Expect "Calibration saved to NVS" and printed offsets. Send `Q` to cancel.
7. **Stabilise** — After drying, pH is polled every 1 s; after 5 consecutive readings in [6.8, 7.2] or after 2 min timeout, transition to READY.

## Sub-phase status

| Sub-Phase | Description              | Status   |
|-----------|--------------------------|----------|
| 1.1       | Project setup, config.h  | Done     |
| 1.2       | Sensor drivers, single-read, NVS calibration | Done     |
| 1.3       | 3-time averaging, delay, optional outlier rejection | Done     |
| 1.4       | State machine (all states and transitions, central tick) | Done     |
| 1.5       | Threshold detection and buzzer alert | Done     |
| 1.6       | Serial JSON log and WiFi HTTP POST with retry | Done     |
| 1.7       | Cleaning station relays (rinse, dryer) | Done     |
| 1.8       | Sensor reset and stabilisation (pH baseline, timeout) | Done     |
| 1.9       | Calibration routine and NVS storage | Done     |
| 1.10      | Integration, testing, documentation | Done     |
