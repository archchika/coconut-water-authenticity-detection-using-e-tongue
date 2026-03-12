/**
 * Cleaning station automation (Phase 1.7, Phase 4.7): rinse, dryer, move-to-station
 * Sequence: move to station (Phase 4.7) -> rinse ON (duration) -> rinse OFF, dryer ON (duration) -> dryer OFF
 */
#ifndef CLEANING_H
#define CLEANING_H

#include <Arduino.h>

/** Call from setup(); sets relay pins (and optional robot pin) OUTPUT and off. */
void cleaning_init(void);

/** Phase 4.7: Command/trigger for robotic arm to move to cleaning station (pulse + wait). Call when entering CLEANING. */
void cleaning_move_to_station(void);

/** Rinse relay: distilled water pump */
void cleaning_rinse_on(void);
void cleaning_rinse_off(void);

/** Dryer relay */
void cleaning_dryer_on(void);
void cleaning_dryer_off(void);

#endif // CLEANING_H
