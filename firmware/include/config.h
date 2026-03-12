/**
 * E-Tongue ESP32 — Central configuration
 * Pin mapping, timing, thresholds, WiFi. Adjust for your hardware.
 */
#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ----- Pin definitions -----
#define PIN_PH_ANALOG      34   // pH sensor (ADC)
#define PIN_TDS_ANALOG     35   // TDS sensor (ADC)
#define PIN_TEMP_ANALOG    36   // Temperature (e.g. NTC or analog out)
#define PIN_TURBIDITY_ANALOG 39 // Turbidity sensor (ADC)

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
// pH: common analog pH (e.g. PH-4502C) ~0.18 V/pH around neutral
#define PH_V_NEUTRAL       2.5f     // Voltage at pH 7
#define PH_V_PER_PH        0.18f    // Volts per pH unit
// TDS: linear approx TDS_ppm = V * factor (e.g. 0.5V -> 100 ppm)
#define TDS_V_TO_PPM       200.0f   // ppm per volt (adjust from datasheet)
// Temperature: LM35-style 10 mV/°C -> temp = V * 100
#define TEMP_V_TO_C        100.0f   // °C per volt (LM35); NTC uses different formula
// Turbidity: linear scale (NTU or relative); higher voltage = more clear on some probes
#define TURB_V_TO_NTU      1000.0f  // Scale factor raw voltage -> NTU (tune)

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
#define TDS_MAX_SAFE       2000.0f   // ppm; adjust for coconut water range
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

// ----- WiFi (for HTTP POST to local ML server) -----
#define WIFI_SSID          "YOUR_FACTORY_SSID"
#define WIFI_PASS          "YOUR_PASSWORD"
#define ML_SERVER_HOST     "192.168.1.100"  // Raspberry Pi / local PC
#define ML_SERVER_PORT     8000
#define ML_POST_PATH       "/api/reading"
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
#define NVS_KEY_TDS_OFFSET "tds_off"
#define NVS_KEY_TEMP_OFFSET "temp_off"
#define NVS_KEY_TURB_OFFSET "turb_off"
// Known reference values when probe is in calibration solution (Phase 1.9)
#define CAL_KNOWN_PH       7.0f   // e.g. pH 7.0 buffer
#define CAL_KNOWN_TDS      0.0f   // distilled water, ppm
#define CAL_KNOWN_TEMP     25.0f  // °C (room temp or measured)
#define CAL_KNOWN_TURB     0.0f   // clear water, NTU

#endif // CONFIG_H
