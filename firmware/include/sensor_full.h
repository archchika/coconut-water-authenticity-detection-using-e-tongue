/**
 * sensor_full — All four sensors: one reading each, every SENSOR_FULL_INTERVAL_MS.
 * Reads pH, TDS, temperature (DS18B20), turbidity once per cycle → one POST to Django.
 */
#ifndef SENSOR_FULL_H
#define SENSOR_FULL_H

#include <Arduino.h>
#include "sensors.h"

typedef struct {
  float ph;
  float tds;
  float temp;
  float turbidity;
  bool ph_detected;
  bool tds_detected;
  bool temp_detected;
  bool turb_detected;
} SensorFullStatus_t;

void sensor_full_init(void);
void sensor_full_tick(void);
void sensor_full_read_and_send(void);
void sensor_full_print_status(void);
SensorFullStatus_t sensor_full_get_status(void);

#endif // SENSOR_FULL_H
