/**
 * E-Tongue state machine (Phase 1.4)
 * IDLE -> DETECTING -> READ_COMPLETE -> CLEANING -> RINSING -> DRYING -> STABILIZE -> READY -> IDLE
 */
#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#include <Arduino.h>
#include "sensors.h"

typedef enum {
  STATE_IDLE,
  STATE_DETECTING,
  STATE_READ_COMPLETE,
  STATE_CLEANING,
  STATE_RINSING,
  STATE_DRYING,
  STATE_STABILIZE,
  STATE_READY,
  STATE_CALIBRATION,
  STATE_COUNT
} State_t;

const char* state_name(State_t s);
void state_set(State_t s);
State_t state_get(void);
void state_machine_init(void);
void state_machine_tick(void);

/** Call from IDLE to start a detection cycle (e.g. from button or serial). */
void state_machine_request_start(void);

/** Copy last averaged reading (valid after READ_COMPLETE). */
void state_machine_get_last_reading(SensorReading_t* out);

#endif // STATE_MACHINE_H
