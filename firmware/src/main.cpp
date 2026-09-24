/**
 * E-Tongue ESP32 — sensor_full mode: pH + TDS + temp + turbidity every 10 s.
 */
#include <Arduino.h>
#include "config.h"
#include "sensors.h"
#include "sensor_full.h"
#include "transport.h"
#include "calibration.h"

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(500);
  Serial.println(F("E-Tongue ESP32 — sensor_full mode (10s cycle)"));
  Serial.println(F("Pins: pH D35 | TDS D32 | Temp D4 | Turb D34"));

  sensors_init();
  transport_wifi_connect();
  transport_wifi_print_status();
  sensor_full_init();

  Serial.println(F("Serial: F=send | P=pH7 water | T=clear turb | Z=reset | W=WiFi | C=cal"));
}

void loop() {
  static bool cal_mode = false;

  sensor_full_tick();

  if (Serial.available()) {
    int c = Serial.read();
    if (cal_mode) {
      if (c == 'S' || c == 's') {
        calibration_run();
        cal_mode = false;
        Serial.println(F("Calibration saved. Resuming 10s cycles."));
      } else if (c == 'Q' || c == 'q') {
        cal_mode = false;
        Serial.println(F("Calibration cancelled."));
      }
    } else if (c == 'W' || c == 'w') {
      transport_wifi_reconnect();
      transport_wifi_print_status();
    } else if (c == 'F' || c == 'f') {
      Serial.println(F("[F] Immediate read + send"));
      sensor_full_read_and_send();
    } else if (c == 'S' || c == 's') {
      sensor_full_print_status();
    } else if (c == 'C' || c == 'c') {
      cal_mode = true;
      calibration_print_help();
    } else if (c == 'Z' || c == 'z') {
      sensors_reset_calibration();
    } else if (c == 'P' || c == 'p') {
      Serial.println(F("[P] pH neutral — use plain/tap water (NOT lemon). Wait 30s, then send P..."));
      sensors_calibrate_ph_neutral();
    } else if (c == 'T' || c == 't') {
      Serial.println(F("[T] Turbidity clear — use plain clear water (NOT lemon). Wait 30s, then send T..."));
      sensors_calibrate_turbidity_clear();
    }
  }

  delay(50);
}
