# E-Tongue ESP32 — State Machine Diagram

**Phase 1.4 / 1.10, Phase 4.7–4.10** — Detection and cleaning cycle; move-to-station; rinse then dryer; stabilisation and reset. **Source of truth for state names and transitions** (Phase 4.10); dashboard and Python use the same names — see `local_dashboard/STATE_ALIGNMENT.md`.

## State diagram (text)

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                                                         │
                    ▼                                                         │
  ┌──────┐   G/C   ┌───────────┐  3× read   ┌───────────────┐   POST/log    │
  │ IDLE │────────►│ DETECTING │────────────►│ READ_COMPLETE │───────────────┼──►┌──────────┐
  └──────┘         └───────────┘             └───────────────┘               │   │ CLEANING │
       ▲                                                                     │   └────┬─────┘
       │                                                                     │        │ move_to_station
       │   reset_flags                                                        │        │ then rinse on
       │                                                                     │        ▼
  ┌────┴────┐   pH stable / timeout   ┌───────────┐   dryer off   ┌────────┐  │   ┌─────────┐
  │  READY  │◄───────────────────────│ STABILIZE │◄──────────────│ DRYING │◄─┼───│ RINSING │
  └─────────┘                         └───────────┘               └────────┘  │   └─────────┘
       │                                    ▲                          ▲      │        │
       │                                    │  N consecutive           │      │        │ rinse off
       └────────────────────────────────────┘  pH in [6.8,7.2]         │      │        │ dryer on
              (or STABILIZE_TIMEOUT_MS)        or timeout               │      │        │
                                               │  RINSE_DURATION_MS     │      │        │
                                               │  DRYER_DURATION_MS     └──────┘        │
```

**CALIBRATION** is a separate state: enter with Serial `C` from IDLE; send `S` to sample and save, or `Q` to quit. No automatic transition.

## Transition table

| From state   | Condition / trigger              | To state     | Action (summary) |
|--------------|----------------------------------|-------------|------------------|
| IDLE        | `state_machine_request_start()`  | DETECTING   | —                |
| DETECTING   | 3× averaged read done            | READ_COMPLETE | Threshold check; buzzer on if out of range |
| READ_COMPLETE | After Serial log + HTTP POST   | CLEANING    | Buzzer off; reading done, data sent to ML |
| CLEANING    | (after move-to-station)          | RINSING     | Phase 4.7: `cleaning_move_to_station()` then rinse ON |
| RINSING     | elapsed ≥ RINSE_DURATION_MS      | DRYING      | Phase 4.8: rinse OFF, dryer ON |
| DRYING      | elapsed ≥ DRYER_DURATION_MS      | STABILIZE   | Phase 4.8: dryer OFF, `stabilise_start()` |
| STABILIZE   | M consecutive pH in [6.8, 7.2] OR timeout | READY | Phase 4.9: `stabilise_tick()`, is_ready/timed_out |
| READY       | (one tick)                       | IDLE        | Phase 4.9: reset flags (buzzer off, stabilise_reset); allow next DETECTING |
| IDLE        | Serial `C` / `c`                 | CALIBRATION | `calibration_print_help()` |
| CALIBRATION | Serial `S` / `s`                | IDLE        | `calibration_run()` |
| CALIBRATION | Serial `Q` / `q`                | IDLE        | Cancel            |

## Module usage per state

| State         | Sensors | Alerts | Transport | Cleaning | Stabilise |
|---------------|---------|--------|-----------|----------|-----------|
| IDLE         | —       | —      | —         | —        | —         |
| DETECTING    | read_averaged | check, buzzer on if fail | — | — | — |
| READ_COMPLETE| get_last_reading | — | serial_log, post_reading | — | — |
| CLEANING     | —       | —      | —         | move_to_station, rinse_on | —         |
| RINSING      | —       | —      | —         | (timing) | —         |
| DRYING       | —       | —      | —         | rinse_off, dryer_on then off | — |
| STABILIZE    | read_ph_raw (via stabilise) | — | — | — | start, tick, is_ready, timed_out |
| READY        | —       | buzzer_off | —       | —        | reset     |

## State name alignment (Phase 4.10)

String names used in JSON (**system_state** / **state**) must match the "From state" column (e.g. IDLE, DETECTING, READ_COMPLETE, CLEANING, RINSING, DRYING, STABILIZE, READY, CALIBRATION). Dashboard mapping: `local_dashboard/STATE_ALIGNMENT.md` and `local_dashboard/state_names.py`.
