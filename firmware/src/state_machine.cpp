/**
 * E-Tongue ESP32 — State machine implementation (Phase 1.4)
 * All states and transitions; central tick drives the flow.
 */
#include "state_machine.h"
#include "config.h"
#include "sensors.h"
#include "alerts.h"
#include "transport.h"
#include "cleaning.h"
#include "stabilise.h"

static const char* const S_NAMES[] = {
  "IDLE", "DETECTING", "READ_COMPLETE", "CLEANING", "RINSING",
  "DRYING", "STABILIZE", "READY", "CALIBRATION"
};

static State_t s_state = STATE_IDLE;
static bool s_start_requested = false;
static SensorReading_t s_last_reading = { 0 };
static SensorReading_t s_batch[ML_BATCH_READINGS];
static unsigned long s_phase_start_ms = 0;       // For RINSING / DRYING duration

const char* state_name(State_t s) {
  if (s >= 0 && s < STATE_COUNT) return S_NAMES[s];
  return "?";
}

void state_set(State_t s) {
  s_state = s;
}

State_t state_get(void) {
  return s_state;
}

void state_machine_request_start(void) {
  s_start_requested = true;
}

void state_machine_get_last_reading(SensorReading_t* out) {
  if (out) *out = s_last_reading;
}

void state_machine_init(void) {
  s_state = STATE_IDLE;
  s_start_requested = false;
  s_phase_start_ms = 0;
  stabilise_reset();
}

void state_machine_tick(void) {
  switch (s_state) {
    case STATE_IDLE:
      if (s_start_requested) {
        s_start_requested = false;
        state_set(STATE_DETECTING);
      }
      break;

    case STATE_DETECTING: {
      // Three snapshots per cycle for backend fusion batch (wireless POST)
      bool any_alert = false;
      for (int i = 0; i < ML_BATCH_READINGS; i++) {
        s_batch[i] = sensors_read_averaged();
        s_last_reading = s_batch[i];
        if (alerts_check_thresholds(&s_batch[i]))
          any_alert = true;
        if (i < ML_BATCH_READINGS - 1)
          delay(ML_BATCH_GAP_MS);
      }
      state_set(STATE_READ_COMPLETE);
      if (any_alert)
        alert_buzzer_on();
      break;
    }

    case STATE_READ_COMPLETE: {
      // Serial log + WiFi POST each snapshot (server buffers 3 → fusion → ML → DB)
      for (int i = 0; i < ML_BATCH_READINGS; i++) {
        const char* row_status = alerts_check_thresholds(&s_batch[i]) ? "threshold_alert" : "unknown";
        transport_serial_log(&s_batch[i], row_status);
        (void)transport_post_reading(&s_batch[i], row_status);
      }
      alert_buzzer_off();  // Silence before cleaning phase
#if SKIP_CLEANING_CYCLE
      state_set(STATE_IDLE);
#else
      state_set(STATE_CLEANING);
#endif
      break;
    }

    case STATE_CLEANING:
      // Phase 4.7: trigger robotic arm to move to cleaning station, then start rinse
      cleaning_move_to_station();
      s_phase_start_ms = millis();
      cleaning_rinse_on();
      state_set(STATE_RINSING);
      break;

    case STATE_RINSING:
      // Phase 4.8: rinse for configured duration, then switch to dryer
      if ((unsigned long)(millis() - s_phase_start_ms) >= (unsigned long)RINSE_DURATION_MS) {
        cleaning_rinse_off();
        cleaning_dryer_on();
        s_phase_start_ms = millis();
        state_set(STATE_DRYING);
      }
      break;

    case STATE_DRYING:
      // Phase 4.8: dryer for configured duration, then go to stabilise
      if ((unsigned long)(millis() - s_phase_start_ms) >= (unsigned long)DRYER_DURATION_MS) {
        cleaning_dryer_off();
        stabilise_start();
        state_set(STATE_STABILIZE);
      }
      break;

    case STATE_STABILIZE:
      // Phase 4.9: wait for pH in baseline range (M consecutive) or timeout
      stabilise_tick();
      if (stabilise_is_ready() || stabilise_timed_out())
        state_set(STATE_READY);
      break;

    case STATE_READY:
      // Phase 4.9: reset flags (alert off, stabilise); set READY then allow next DETECTING cycle
      alert_buzzer_off();
      stabilise_reset();
      state_set(STATE_IDLE);
      break;

    case STATE_CALIBRATION:
      // Phase 1.9: calibration routine; no auto transition
      break;

    default:
      break;
  }
}
