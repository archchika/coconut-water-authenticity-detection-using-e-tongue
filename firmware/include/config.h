/**
 * E-Tongue ESP32 — Central configuration
 * Pin mapping, timing, thresholds, WiFi. Adjust for your hardware.
 */
#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ----- Pin definitions (one sensor per GPIO — do NOT share pins) -----
//   pH         → D35 (GPIO 35)
//   TDS        → D32 (GPIO 32) — move wire from D3; D3 is NOT ADC on ESP32
//   Temp       → D4  (GPIO 4)  — DS18B20 + 4.7k pull-up to 3.3V
//   Turbidity  → D34 (GPIO 34) — stays here (NOT D35; pH uses D35)
#define ENABLE_PH_SENSOR     1
#define PIN_PH_ANALOG        35   // D35 — pH only

#define PIN_TDS_ANALOG       3    // D3 — invalid ADC; do not use
#define PIN_TDS_ANALOG_ALT   32   // D32 — wire TDS signal here
#define USE_TDS_PIN_ALT      1    // TDS on D32 (D35 reserved for pH)
#define PIN_TEMP_ONEWIRE     4    // D4 — DS18B20
#define PIN_TURBIDITY_ANALOG 34   // D34 — turbidity (keep on D34, not D35)

#define PH_PLACEHOLDER       5.2f // Used only when ENABLE_PH_SENSOR=0

#define PIN_BUZZER         25   // Buzzer for local alert
#define PIN_RINSE_RELAY    26   // Distilled water pump / rinse
#define PIN_DRYER_RELAY    27   // Dryer control
// Phase 4.7: optional trigger for robotic arm to move to cleaning station
#define USE_ROBOT_MOVE_STATION   1     // 0 = no-op (no pin); 1 = pulse then wait
#define PIN_ROBOT_MOVE_STATION   33    // GPIO for move-to-station trigger (used when USE_ROBOT_MOVE_STATION)
#define MOVE_TO_STATION_PULSE_MS 200   // Pulse length (ms) for robot controller
#define MOVE_TO_STATION_WAIT_MS  3000  // Wait (ms) for arm to reach station before rinse

#define ADC_RESOLUTION     4096.0f  // ESP32 12-bit
#define ADC_VREF           3.3f

// ----- ADC -> physical unit conversion (tune for your probes) -----
// pH PH-4502C Po: voltage falls as pH rises → pH = 7 + (V_at_pH7 - V) / 0.059
#define PH_FORMULA_GRAVITY     0     // 0 = Nernst (correct for most Po probes)
#define PH_V_AT_7_DEFAULT      2.50f // Typical PH-4502C Po at pH 7 (~2.5 V); override with Serial P
#define PH_V_PER_PH            0.059f // 59 mV per pH unit at 25 °C
// TDS: linear approx TDS_ppm = V * factor (e.g. 0.5V -> 100 ppm)
#define TDS_V_TO_PPM       200.0f   // ppm per volt (adjust from datasheet)
// Temperature: LM35-style 10 mV/°C -> temp = V * 100
#define TEMP_V_TO_C        100.0f   // °C per volt (LM35); NTC uses different formula
// Turbidity: DFRobot-style — voltage drops as water gets cloudier (calibrate clear water with T)
#define TURB_V_CLEAR_DEFAULT   2.10f  // Typical clear-water voltage at 3.3 V ADC (use T to teach)
#define TURB_NTU_PER_VOLT      850.0f // NTU per volt below clear baseline
#define TURB_V_TO_NTU          1000.0f // Legacy linear scale (unused when baseline formula enabled)

// ----- Sensor read timing -----
#define READ_DELAY_MS      500  // Delay between each of the 3 reads per sensor
#define NUM_READS          3    // 3-time averaging
#define SENSORS_REJECT_OUTLIERS 0  // 1 = median of 3 (reject outliers); 0 = mean of 3

// ----- Thresholds (sensor raw or converted; tune from calibration) -----
#define PH_MIN_SAFE        4.5f
#define PH_MAX_SAFE        7.0f
#define PH_BASELINE_MIN    6.8f  // After cleaning: expect ~neutral
#define PH_BASELINE_MAX    7.2f
#define TDS_MIN_SAFE       0.0f
#define TDS_MAX_SAFE       6000.0f   // ppm; coconut water can exceed 2000
#define TEMP_MIN_SAFE      10.0f    // °C
#define TEMP_MAX_SAFE      50.0f
#define TURBIDITY_MIN_SAFE 0.0f
#define TURBIDITY_MAX_SAFE 3000.0f  // NTU or raw; adjust

// ----- Cleaning automation (Phase 4.8: rinse then dryer for configured duration) -----
#define RINSE_DURATION_MS  10000   // 10 s — distilled water rinse
#define DRYER_DURATION_MS  30000   // 30 s — dryer ON
// Phase 4.9: M consecutive pH in baseline (e.g. 6.8–7.2) over N seconds; then READY
#define STABILIZE_READINGS 5       // M — consecutive pH readings in baseline range
#define STABILIZE_INTERVAL_MS 1000 // Check pH every N seconds (1 s)
#define STABILIZE_TIMEOUT_MS 120000 // Max wait for pH baseline (2 min); then allow READY anyway

// ----- sensor_full module: one read each → one POST every 10 s -----
#define USE_SENSOR_FULL_MODULE   1
#define SENSOR_FULL_INTERVAL_MS  10000  // 10 seconds between full sensor cycles

// ----- Measurement cycle (legacy state machine — off when USE_SENSOR_FULL_MODULE=1) -----
#define SKIP_CLEANING_CYCLE  1
#define AUTO_MEASURE_INTERVAL_MS  0

// ----- WiFi (for HTTP POST to local ML server) -----
#define ML_BATCH_READINGS  1     // One combined reading per POST (sensor_full mode)
#define ML_BATCH_GAP_MS    500   // Delay between batch snapshots (ms)
#define WIFI_SSID          "maha"
#define WIFI_PASS          "12345678"
#define ML_SERVER_HOST     "10.216.217.31"
#define ML_SERVER_PORT     8000
#define ML_POST_PATH       "/api/esp32-reading/"
#define SOURCE_DEVICE_ID   "esp32-01"
#define WIFI_CONNECT_TIMEOUT_MS  10000
// Phase 5.2: retry with backoff; log failures locally
#define TRANSPORT_POST_RETRIES   3
#define TRANSPORT_POST_RETRY_DELAY_MS 1000   // Base delay; actual = delay * (1 << attempt)

// ----- Serial -----
#define SERIAL_BAUD        115200

// ----- Calibration (stored in NVS after calibration routine) -----
// Offsets applied: reading_corrected = reading_raw + offset
#define NVS_NAMESPACE      "etongue"
#define NVS_KEY_PH_OFFSET  "ph_off"
#define NVS_KEY_PH_V7      "ph_v7"
#define NVS_KEY_TURB_VCLR  "turb_v0"
#define NVS_KEY_TDS_OFFSET "tds_off"
#define NVS_KEY_TEMP_OFFSET "temp_off"
#define NVS_KEY_TURB_OFFSET "turb_off"
// Known reference values when probe is in calibration solution (Phase 1.9)
#define CAL_KNOWN_PH       7.0f   // e.g. pH 7.0 buffer
#define CAL_KNOWN_TDS      0.0f   // distilled water, ppm
#define CAL_KNOWN_TEMP     25.0f  // °C (room temp or measured)
#define CAL_KNOWN_TURB     0.0f   // clear water, NTU

#endif // CONFIG_H
