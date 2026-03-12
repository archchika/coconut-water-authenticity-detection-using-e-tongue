/**
 * Threshold check and buzzer alert (Phase 1.5)
 */
#ifndef ALERTS_H
#define ALERTS_H

#include <Arduino.h>
#include "sensors.h"

/** Call once from setup(); sets buzzer pin as OUTPUT and off. */
void alerts_init(void);

/** Returns true if any channel is out of safe range (config.h). */
bool alerts_check_thresholds(const SensorReading_t* r);

/** Buzzer: on/off */
void alert_buzzer_on(void);
void alert_buzzer_off(void);

/** Call when ML says adulterated (e.g. from Phase 1.6); turns buzzer on. */
void alert_adulteration(void);

#endif // ALERTS_H
