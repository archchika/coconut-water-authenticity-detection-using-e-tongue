/**
 * E-Tongue ESP32 — Calibration routine and NVS storage (Phase 1.9)
 */
#include "calibration.h"
#include "config.h"
#include "sensors.h"

void calibration_print_help(void) {
  Serial.println(F("=== Calibration mode ==="));
  Serial.println(F("Place probe in known solution (e.g. pH 7 buffer / distilled water)."));
  Serial.println(F("Then send 'S' to sample and save offsets to NVS."));
  Serial.println(F("Send 'Q' to quit without saving."));
  Serial.print(F("Known ref: pH=")); Serial.print(CAL_KNOWN_PH);
  Serial.print(F(" TDS=")); Serial.print(CAL_KNOWN_TDS);
  Serial.print(F(" T=")); Serial.print(CAL_KNOWN_TEMP);
  Serial.print(F(" Turb=")); Serial.println(CAL_KNOWN_TURB);
}

bool calibration_run(void) {
  SensorReading_t r = sensors_read_averaged_uncalibrated();
  float ph_off   = CAL_KNOWN_PH   - r.ph;
  float tds_off  = CAL_KNOWN_TDS  - r.tds;
  float temp_off = CAL_KNOWN_TEMP - r.temp;
  float turb_off = CAL_KNOWN_TURB - r.turbidity;

  sensors_save_calibration(ph_off, tds_off, temp_off, turb_off);

  Serial.println(F("Calibration saved to NVS."));
  Serial.print(F("  Offsets: pH=")); Serial.print(ph_off);
  Serial.print(F(" TDS=")); Serial.print(tds_off);
  Serial.print(F(" T=")); Serial.print(temp_off);
  Serial.print(F(" Turb=")); Serial.println(turb_off);
  return true;
}
