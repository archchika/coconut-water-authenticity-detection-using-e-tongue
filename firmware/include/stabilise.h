/**
 * Sensor reset and stabilisation (Phase 1.8, Phase 4.9)
 * After drying: poll pH until within baseline range for M consecutive samples (over N seconds);
 * then allow READY. Reset flags (alert off, stabilise counter) and allow next DETECTING cycle.
 */
#ifndef STABILISE_H
#define STABILISE_H

#include <Arduino.h>

/** Call when entering STABILIZE state; resets counter and start time. */
void stabilise_start(void);

/** Call every loop while in STABILIZE; reads pH at interval and updates state. */
void stabilise_tick(void);

/** True when N consecutive pH readings are in baseline range (PH_BASELINE_MIN..MAX). */
bool stabilise_is_ready(void);

/** True when STABILIZE_TIMEOUT_MS elapsed without stabilising; allow READY anyway. */
bool stabilise_timed_out(void);

/** Call when leaving STABILIZE or in READY; reset for next cycle. */
void stabilise_reset(void);

#endif // STABILISE_H
