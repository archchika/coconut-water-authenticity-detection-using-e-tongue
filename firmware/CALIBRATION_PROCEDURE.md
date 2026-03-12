# E-Tongue ESP32 — Calibration Procedure

**Phase 1.9 / 1.10** — Operator procedure for sensor calibration and NVS storage.

## When to calibrate

- After first installation or sensor replacement.
- If readings drift (e.g. pH consistently off from known samples).
- Periodically (e.g. weekly) if required by your quality procedure.

## Prerequisites

- ESP32 powered and connected via USB (Serial monitor at 115200 baud).
- Known reference solution(s). Default assumptions in firmware:
  - **pH 7.0** buffer (e.g. standard buffer solution).
  - **TDS 0** (distilled or deionised water).
  - **Temperature 25 °C** (room temp or measure and update `CAL_KNOWN_TEMP` in `config.h`).
  - **Turbidity 0** (clear water).
- If your reference values differ, edit `include/config.h` before calibration:
  - `CAL_KNOWN_PH`, `CAL_KNOWN_TDS`, `CAL_KNOWN_TEMP`, `CAL_KNOWN_TURB`.

## Step-by-step

1. **Open Serial monitor**  
   - 115200 baud. You should see: `E-Tongue ESP32 — Phase 1.9 calibration ready` and state `IDLE`.

2. **Enter calibration mode**  
   - Send **`C`** (or **`c`**).  
   - The device prints instructions and the current known reference values (pH, TDS, T, Turb).

3. **Prepare the probe**  
   - Rinse the probe with distilled water and gently blot (do not rub the sensing surfaces).  
   - Place the probe in the **known reference solution** (e.g. pH 7.0 buffer in a small beaker).  
   - Allow **at least 30 seconds** for the reading to settle (optional but recommended).

4. **Take and save the calibration**  
   - Send **`S`** (or **`s`**).  
   - The firmware takes a **3× averaged** reading (uncalibrated), computes offsets as `known − reading` for each channel, and **saves them to NVS**.  
   - Serial will show: `Calibration saved to NVS.` and the four offsets (pH, TDS, T, Turb).

5. **Exit without saving (optional)**  
   - To leave calibration without saving, send **`Q`** (or **`q`**).  
   - Device returns to `IDLE`; no NVS change.

6. **Verify**  
   - After saving, the next detection cycle will use the new offsets (loaded on boot and after `sensors_save_calibration`).  
   - Run a sample in a known solution and confirm values are close to expected.

## Notes

- Calibration uses **one point per channel** (single reference solution). For higher accuracy, use a reference close to your typical measurement range (e.g. pH 5–6 for coconut water).
- Offsets are stored in **NVS** (non-volatile) and survive power cycle; they are loaded in `setup()` via `sensors_load_calibration()`.
- To reset offsets to zero without re-flashing: run calibration with a solution that gives the same reading as your current “raw” (e.g. adjust `CAL_KNOWN_*` so that `known − reading = 0`), or add a separate “reset calibration” command in code if needed.
