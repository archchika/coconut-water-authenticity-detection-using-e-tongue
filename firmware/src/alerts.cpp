/**
 * E-Tongue ESP32 — Threshold detection and buzzer alert (Phase 1.5)
 */
#include "alerts.h"
#include "config.h"

void alerts_init(void) {
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
}

bool alerts_check_thresholds(const SensorReading_t* r) {
  if (!r) return false;
  if (r->ph < PH_MIN_SAFE || r->ph > PH_MAX_SAFE) return true;
  if (r->tds < TDS_MIN_SAFE || r->tds > TDS_MAX_SAFE) return true;
  if (r->temp < TEMP_MIN_SAFE || r->temp > TEMP_MAX_SAFE) return true;
  if (r->turbidity < TURBIDITY_MIN_SAFE || r->turbidity > TURBIDITY_MAX_SAFE) return true;
  return false;
}

void alert_buzzer_on(void) {
  digitalWrite(PIN_BUZZER, HIGH);
}

void alert_buzzer_off(void) {
  digitalWrite(PIN_BUZZER, LOW);
}

void alert_adulteration(void) {
  alert_buzzer_on();
}
