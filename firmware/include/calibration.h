/**
 * Calibration routine and NVS storage (Phase 1.9)
 * Record known sample (e.g. buffer), compute offsets, save to NVS.
 */
#ifndef CALIBRATION_H
#define CALIBRATION_H

#include <Arduino.h>

/** Print instructions to Serial (place probe, send S). */
void calibration_print_help(void);

/**
 * Take averaged uncalibrated reading, compute offsets (known - reading),
 * save to NVS. Uses CAL_KNOWN_* from config.h.
 * Returns true on success.
 */
bool calibration_run(void);

#endif // CALIBRATION_H
