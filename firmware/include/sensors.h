/**
 * E-Tongue sensor reading and 3-time averaging
 * pH, TDS, Temperature, Turbidity
 */
#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>

typedef struct {
  float ph;
  float tds;
  float temp;
  float turbidity;
} SensorReading_t;

// DS18B20 + ADC init (call from setup)
void sensors_init(void);

// One-time read (raw ADC -> physical units; apply calibration offsets in implementation)
float read_ph_raw(void);
float read_tds_raw(void);
float read_temp_raw(void);
float read_turbidity_raw(void);

// 3-time average and optional outlier rejection; returns mean
SensorReading_t sensors_read_averaged(void);

// Same as above but without applying stored offsets (for calibration routine)
SensorReading_t sensors_read_averaged_uncalibrated(void);

// Load/save calibration offsets from NVS (used by calibration routine)
void sensors_load_calibration(void);
void sensors_save_calibration(float ph_off, float tds_off, float temp_off, float turb_off);

/** Clear NVS calibration offsets (Serial Z). */
void sensors_reset_calibration(void);

/** Put probe in pH~7 water, call this (Serial P) — saves neutral voltage. */
void sensors_calibrate_ph_neutral(void);

/** Put probe in clear water, call this (Serial T) — saves turbidity zero baseline voltage. */
void sensors_calibrate_turbidity_clear(void);

/** Print one averaged reading to Serial (debug). */
void sensors_print_reading(const char* label);

#endif // SENSORS_H
