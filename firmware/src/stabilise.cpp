/**
 * E-Tongue ESP32 — Sensor reset and stabilisation (Phase 1.8, Phase 4.9)
 * Phase 4.9: Wait for pH in baseline range (PH_BASELINE_MIN..MAX) for M consecutive
 * samples (STABILIZE_READINGS) at STABILIZE_INTERVAL_MS; or until STABILIZE_TIMEOUT_MS.
 */
#include "stabilise.h"
#include "config.h"
#include "sensors.h"

static uint8_t s_count = 0;
static unsigned long s_start_ms = 0;
static unsigned long s_last_check_ms = 0;

void stabilise_start(void) {
  s_count = 0;
  s_start_ms = millis();
  s_last_check_ms = s_start_ms;
}

void stabilise_tick(void) {
  unsigned long now = millis();
  if ((unsigned long)(now - s_last_check_ms) < (unsigned long)STABILIZE_INTERVAL_MS)
    return;
  s_last_check_ms = now;

  float ph = read_ph_raw();
  if (ph >= PH_BASELINE_MIN && ph <= PH_BASELINE_MAX) {
    s_count++;
  } else {
    s_count = 0;
  }
}

bool stabilise_is_ready(void) {
  return s_count >= STABILIZE_READINGS;
}

bool stabilise_timed_out(void) {
  return (unsigned long)(millis() - s_start_ms) >= (unsigned long)STABILIZE_TIMEOUT_MS;
}

void stabilise_reset(void) {
  s_count = 0;
}
