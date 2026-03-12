/**
 * E-Tongue ESP32 — Sensor drivers (Phase 1.2) and 3-time averaging (Phase 1.3)
 * One-shot read: ADC -> physical units; calibration from NVS.
 * Averaging: NUM_READS with READ_DELAY_MS; mean or median (outlier rejection).
 */
#include "sensors.h"
#include "config.h"
#include <Preferences.h>

// Calibration offsets: reading_corrected = reading_raw + offset (loaded from NVS)
static float s_offset_ph   = 0.0f;
static float s_offset_tds  = 0.0f;
static float s_offset_temp  = 0.0f;
static float s_offset_turb = 0.0f;

static bool s_cal_loaded = false;

// ADC raw to voltage (0..3.3 V)
static inline float adc_to_voltage(int raw) {
  return (raw / ADC_RESOLUTION) * ADC_VREF;
}

static void ensure_calibration_loaded(void) {
  if (s_cal_loaded) return;
  sensors_load_calibration();
  s_cal_loaded = true;
}

// ----- One-shot read: ADC -> physical value + offset -----

float read_ph_raw(void) {
  ensure_calibration_loaded();
  int raw = analogRead(PIN_PH_ANALOG);
  float V = adc_to_voltage(raw);
  // pH = 7 + (2.5 - V) / 0.18 (common analog pH probe)
  float ph = 7.0f + (PH_V_NEUTRAL - V) / PH_V_PER_PH;
  return ph + s_offset_ph;
}

float read_tds_raw(void) {
  ensure_calibration_loaded();
  int raw = analogRead(PIN_TDS_ANALOG);
  float V = adc_to_voltage(raw);
  float tds_ppm = V * TDS_V_TO_PPM;
  return tds_ppm + s_offset_tds;
}

float read_temp_raw(void) {
  ensure_calibration_loaded();
  int raw = analogRead(PIN_TEMP_ANALOG);
  float V = adc_to_voltage(raw);
  // LM35-style: 10 mV/°C -> temp = V * 100
  float temp_c = V * TEMP_V_TO_C;
  return temp_c + s_offset_temp;
}

float read_turbidity_raw(void) {
  ensure_calibration_loaded();
  int raw = analogRead(PIN_TURBIDITY_ANALOG);
  float V = adc_to_voltage(raw);
  float ntu = V * TURB_V_TO_NTU;
  return ntu + s_offset_turb;
}

// ----- Uncalibrated reads (no offset; for calibration routine) -----
static float read_ph_uncal(void) {
  int raw = analogRead(PIN_PH_ANALOG);
  float V = adc_to_voltage(raw);
  return 7.0f + (PH_V_NEUTRAL - V) / PH_V_PER_PH;
}
static float read_tds_uncal(void) {
  int raw = analogRead(PIN_TDS_ANALOG);
  float V = adc_to_voltage(raw);
  return V * TDS_V_TO_PPM;
}
static float read_temp_uncal(void) {
  int raw = analogRead(PIN_TEMP_ANALOG);
  float V = adc_to_voltage(raw);
  return V * TEMP_V_TO_C;
}
static float read_turb_uncal(void) {
  int raw = analogRead(PIN_TURBIDITY_ANALOG);
  float V = adc_to_voltage(raw);
  return V * TURB_V_TO_NTU;
}

// ----- 3-time averaging with delay; optional median (outlier rejection) -----
static float average_n_reads(float (*read_fn)(void)) {
  float buf[NUM_READS];
  for (int i = 0; i < NUM_READS; i++) {
    buf[i] = read_fn();
    if (i < NUM_READS - 1) delay(READ_DELAY_MS);
  }
#if SENSORS_REJECT_OUTLIERS
  // Median of 3: sort and take middle
  for (int i = 0; i < NUM_READS - 1; i++)
    for (int j = i + 1; j < NUM_READS; j++)
      if (buf[j] < buf[i]) { float t = buf[i]; buf[i] = buf[j]; buf[j] = t; }
  return buf[NUM_READS / 2];
#else
  float sum = 0.0f;
  for (int i = 0; i < NUM_READS; i++) sum += buf[i];
  return sum / (float)NUM_READS;
#endif
}

SensorReading_t sensors_read_averaged(void) {
  SensorReading_t r;
  r.ph        = average_n_reads(read_ph_raw);
  r.tds       = average_n_reads(read_tds_raw);
  r.temp      = average_n_reads(read_temp_raw);
  r.turbidity = average_n_reads(read_turbidity_raw);
  return r;
}

SensorReading_t sensors_read_averaged_uncalibrated(void) {
  SensorReading_t r;
  r.ph        = average_n_reads(read_ph_uncal);
  r.tds       = average_n_reads(read_tds_uncal);
  r.temp      = average_n_reads(read_temp_uncal);
  r.turbidity = average_n_reads(read_turb_uncal);
  return r;
}

// ----- NVS calibration load/save -----
void sensors_load_calibration(void) {
  Preferences prefs;
  if (!prefs.begin(NVS_NAMESPACE, true)) return;
  s_offset_ph   = prefs.getFloat(NVS_KEY_PH_OFFSET, 0.0f);
  s_offset_tds  = prefs.getFloat(NVS_KEY_TDS_OFFSET, 0.0f);
  s_offset_temp = prefs.getFloat(NVS_KEY_TEMP_OFFSET, 0.0f);
  s_offset_turb = prefs.getFloat(NVS_KEY_TURB_OFFSET, 0.0f);
  prefs.end();
  s_cal_loaded = true;
}

void sensors_save_calibration(float ph_off, float tds_off, float temp_off, float turb_off) {
  Preferences prefs;
  if (!prefs.begin(NVS_NAMESPACE, false)) return;
  prefs.putFloat(NVS_KEY_PH_OFFSET, ph_off);
  prefs.putFloat(NVS_KEY_TDS_OFFSET, tds_off);
  prefs.putFloat(NVS_KEY_TEMP_OFFSET, temp_off);
  prefs.putFloat(NVS_KEY_TURB_OFFSET, turb_off);
  prefs.end();
  s_offset_ph   = ph_off;
  s_offset_tds  = tds_off;
  s_offset_temp = temp_off;
  s_offset_turb = turb_off;
  s_cal_loaded = true;
}
