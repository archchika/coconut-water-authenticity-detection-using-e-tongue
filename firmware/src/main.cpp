/**
 * E-Tongue ESP32 — Main entry (Phase 1.10 integration)
 *
 * Setup: sensors (load NVS cal), alerts, cleaning, state_machine, transport (WiFi).
 * Loop: state_machine_tick(); Serial commands (G=start, C=calibration, S=save, Q=quit);
 *       state change and READ_COMPLETE printing.
 * See STATE_DIAGRAM.md and CALIBRATION_PROCEDURE.md.
 */
#include <Arduino.h>
#include "config.h"
#include "sensors.h"
#include "state_machine.h"
#include "alerts.h"
#include "transport.h"
#include "cleaning.h"
#include "calibration.h"

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(500);
  Serial.println(F("E-Tongue ESP32 — Phase 1.9 calibration ready"));
  sensors_load_calibration();
  alerts_init();
  cleaning_init();
  state_machine_init();
  transport_wifi_connect();
}

void loop() {
  state_machine_tick();

  // Optional: request start via Serial (send 'G' or 'g') or auto-start once after 5 s in IDLE
  static unsigned long last_auto_start = 0;
  if (state_get() == STATE_IDLE) {
    if (last_auto_start == 0) last_auto_start = millis();
    if (Serial.available()) {
      int c = Serial.read();
      if (c == 'G' || c == 'g') state_machine_request_start();
      else if (c == 'C' || c == 'c') {
        state_set(STATE_CALIBRATION);
        calibration_print_help();
      }
    }
    else if ((unsigned long)(millis() - last_auto_start) > 5000) {
      state_machine_request_start();
      last_auto_start = millis();
    }
  } else if (state_get() == STATE_CALIBRATION) {
    if (Serial.available()) {
      int c = Serial.read();
      if (c == 'S' || c == 's') {
        calibration_run();
        state_set(STATE_IDLE);
      } else if (c == 'Q' || c == 'q') {
        Serial.println(F("Calibration cancelled."));
        state_set(STATE_IDLE);
      }
    }
  } else {
    last_auto_start = 0;
  }

  // Print state and, when READ_COMPLETE, last reading
  static State_t prev_state = STATE_COUNT;
  if (state_get() != prev_state) {
    prev_state = state_get();
    Serial.println(state_name(state_get()));
    if (state_get() == STATE_READ_COMPLETE) {
      SensorReading_t r;
      state_machine_get_last_reading(&r);
      Serial.print(F("  pH=")); Serial.print(r.ph);
      Serial.print(F(" TDS=")); Serial.print(r.tds);
      Serial.print(F(" T=")); Serial.print(r.temp);
      Serial.print(F(" Turb=")); Serial.println(r.turbidity);
    }
  }

  delay(100);
}
