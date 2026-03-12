# State machine alignment (Phase 4.10)

Canonical state names and transitions are defined in the **firmware**; the dashboard and any Python automation use the same names for the **system_state** / **state** field.

## Source of truth

- **Transitions and behaviour:** [firmware/STATE_DIAGRAM.md](../firmware/STATE_DIAGRAM.md)
- **Firmware enum:** `firmware/include/state_machine.h` — `State_t` (STATE_IDLE, STATE_DETECTING, …)
- **Firmware string names:** `state_machine.cpp` — `S_NAMES[]` (IDLE, DETECTING, READ_COMPLETE, CLEANING, RINSING, DRYING, STABILIZE, READY, CALIBRATION)

## State name alignment

When the gateway or ESP32 includes **system_state** or **state** in the JSON reading, it must use one of these **exact** strings (case-insensitive for display):

| Firmware (C enum / string) | JSON value (`system_state` / `state`) | Dashboard display label |
|----------------------------|----------------------------------------|-------------------------|
| STATE_IDLE                 | IDLE                                   | Idle                    |
| STATE_DETECTING            | DETECTING                              | Detecting               |
| STATE_READ_COMPLETE        | READ_COMPLETE                          | Read complete           |
| STATE_CLEANING             | CLEANING                               | Cleaning                |
| STATE_RINSING              | RINSING                                | Rinsing                 |
| STATE_DRYING               | DRYING                                 | Drying                  |
| STATE_STABILIZE            | STABILIZE                              | Stabilising             |
| STATE_READY                | READY                                  | Ready                   |
| STATE_CALIBRATION          | CALIBRATION                            | Calibration             |

## Python usage

- **local_dashboard/state_names.py** defines the same state string constants (`STATE_IDLE`, `STATE_DETECTING`, …) and **STATE_DISPLAY_LABELS**, and provides **state_to_display_label(raw_state, has_reading)** for the UI.
- Use **state_names.py** in any Python automation or gateway code that needs to interpret or emit the same state values.

## Transition summary

See [firmware/STATE_DIAGRAM.md](../firmware/STATE_DIAGRAM.md) for the full table. Short flow:

- **IDLE** → (start) → **DETECTING** → **READ_COMPLETE** → **CLEANING** → **RINSING** → **DRYING** → **STABILIZE** → **READY** → **IDLE**
- **IDLE** → (Serial `C`) → **CALIBRATION** → (Serial `S`/`Q`) → **IDLE**
