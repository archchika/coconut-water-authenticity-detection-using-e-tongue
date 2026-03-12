/**
 * E-Tongue ESP32 — Cleaning station relay control (Phase 1.7, Phase 4.7, Phase 4.8)
 * Phase 4.8: rinse relay ON for RINSE_DURATION_MS, then dryer ON for DRYER_DURATION_MS (state machine).
 */
#include "cleaning.h"
#include "config.h"

void cleaning_init(void) {
  pinMode(PIN_RINSE_RELAY, OUTPUT);
  pinMode(PIN_DRYER_RELAY, OUTPUT);
  digitalWrite(PIN_RINSE_RELAY, LOW);
  digitalWrite(PIN_DRYER_RELAY, LOW);
#if USE_ROBOT_MOVE_STATION
  pinMode(PIN_ROBOT_MOVE_STATION, OUTPUT);
  digitalWrite(PIN_ROBOT_MOVE_STATION, LOW);
#endif
}

void cleaning_move_to_station(void) {
#if USE_ROBOT_MOVE_STATION
  digitalWrite(PIN_ROBOT_MOVE_STATION, HIGH);
  delay(MOVE_TO_STATION_PULSE_MS);
  digitalWrite(PIN_ROBOT_MOVE_STATION, LOW);
  delay(MOVE_TO_STATION_WAIT_MS);
#else
  (void)0;
#endif
}

void cleaning_rinse_on(void) {
  digitalWrite(PIN_RINSE_RELAY, HIGH);
}

void cleaning_rinse_off(void) {
  digitalWrite(PIN_RINSE_RELAY, LOW);
}

void cleaning_dryer_on(void) {
  digitalWrite(PIN_DRYER_RELAY, HIGH);
}

void cleaning_dryer_off(void) {
  digitalWrite(PIN_DRYER_RELAY, LOW);
}
