/**
 * E-Tongue ESP32 — Sensor drivers (Phase 1.2) and 3-time averaging (Phase 1.3)
 * pH optional; TDS + turbidity analog; DS18B20 on OneWire (D4).
 */
#include "sensors.h"
#include "config.h"
#include <Preferences.h>
#include <OneWire.h>
#include <DallasTemperature.h>

static OneWire s_oneWire(PIN_TEMP_ONEWIRE);
static DallasTemperature s_ds18b20(&s_oneWire);
static bool s_ds18b20_ready = false;

static float s_offset_ph   = 0.0f;
static float s_offset_tds  = 0.0f;
static float s_offset_temp  = 0.0f;
static float s_offset_turb = 0.0f;
static float s_ph_v_at_7   = PH_V_AT_7_DEFAULT;
static float s_turb_v_clear = TURB_V_CLEAR_DEFAULT;

static bool s_cal_loaded = false;

static int tds_adc_pin(void) {
#if USE_TDS_PIN_ALT
  return PIN_TDS_ANALOG_ALT;
#else
  return PIN_TDS_ANALOG;
#endif
}

static inline float adc_to_voltage(int raw) {
  return (raw / ADC_RESOLUTION) * ADC_VREF;
}

static void sensors_adc_init(void) {
  analogReadResolution(12);
#if defined(ADC_11db)
  analogSetAttenuation(ADC_11db);
#endif
}

static float ph_v7_reference(void) {
  return (s_ph_v_at_7 > 0.01f) ? s_ph_v_at_7 : PH_V_AT_7_DEFAULT;
}

static float turb_clear_reference(void) {
  return (s_turb_v_clear > 0.01f) ? s_turb_v_clear : TURB_V_CLEAR_DEFAULT;
}

static float ph_from_voltage(float V) {
#if PH_FORMULA_GRAVITY
  float ph = PH_SLOPE * V + PH_INTERCEPT;
#else
  float v7 = ph_v7_reference();
  float ph = 7.0f + (v7 - V) / PH_V_PER_PH;
#endif
  if (ph < 0.0f) ph = 0.0f;
  if (ph > 14.0f) ph = 14.0f;
  return ph;
}

static float turbidity_from_voltage(float V) {
  float v_clear = turb_clear_reference();
  float ntu = (v_clear - V) * TURB_NTU_PER_VOLT;
  if (ntu < 0.0f) ntu = 0.0f;
  if (ntu > TURBIDITY_MAX_SAFE) ntu = TURBIDITY_MAX_SAFE;
  return ntu;
}

static float read_ph_voltage(void) {
  int raw = analogRead(PIN_PH_ANALOG);
  return adc_to_voltage(raw);
}

static void ensure_calibration_loaded(void) {
  if (s_cal_loaded) return;
  sensors_load_calibration();
  s_cal_loaded = true;
}

void sensors_init(void) {
  sensors_adc_init();
  sensors_load_calibration();
  s_ds18b20.begin();
  s_ds18b20.setWaitForConversion(false);
  s_ds18b20.requestTemperatures();
  delay(750);
  float t = s_ds18b20.getTempCByIndex(0);
  s_ds18b20_ready = (t != DEVICE_DISCONNECTED_C && t != -127.0f);
  if (!s_ds18b20_ready) {
    Serial.println(F("[sensors] DS18B20 not detected on D4 — check wiring + 4.7k pull-up"));
  } else {
    Serial.printf("[sensors] DS18B20 OK on D4 (%.1f C)\n", t);
  }
#if !USE_TDS_PIN_ALT
  Serial.println(F("[sensors] TDS on D3/GPIO3 — NOT ADC; set USE_TDS_PIN_ALT=1 and wire TDS to D32"));
#else
  Serial.printf("[sensors] TDS on D%d (GPIO%d)\n", PIN_TDS_ANALOG_ALT, PIN_TDS_ANALOG_ALT);
#endif
  int tdsRaw = analogRead(tds_adc_pin());
  int turbRaw = analogRead(PIN_TURBIDITY_ANALOG);
  Serial.printf("[sensors] ADC raw: TDS pin=%d raw=%d | Turb D34 raw=%d\n", tds_adc_pin(), tdsRaw, turbRaw);
#if ENABLE_PH_SENSOR
  int phRaw = analogRead(PIN_PH_ANALOG);
  float phV = adc_to_voltage(phRaw);
  float phEst = ph_from_voltage(phV);
  if (s_ph_v_at_7 <= 0.01f) {
    Serial.printf("[sensors] pH GPIO%d raw=%d V=%.3f est=%.2f — send P in plain water (not lemon)\n",
                  PIN_PH_ANALOG, phRaw, phV, phEst);
  } else {
    Serial.printf("[sensors] pH GPIO%d raw=%d V=%.3f est=%.2f (V7=%.3f offset=%.3f)\n",
                  PIN_PH_ANALOG, phRaw, phV, phEst, s_ph_v_at_7, s_offset_ph);
  }
#endif
  float turbV = adc_to_voltage(turbRaw);
  Serial.printf("[sensors] Turb GPIO%d raw=%d V=%.3f est=%.1f NTU (clear V=%.3f) — send T in clear water\n",
                PIN_TURBIDITY_ANALOG, turbRaw, turbV,
                turbidity_from_voltage(turbV), turb_clear_reference());
  if (turbRaw < 50) {
    Serial.println(F("[sensors] WARNING: turbidity ADC near 0 — check D34 wiring + sensor power"));
  }
}

static float read_ds18b20_c(void) {
  s_ds18b20.requestTemperatures();
  delay(750);
  float t = s_ds18b20.getTempCByIndex(0);
  if (t == DEVICE_DISCONNECTED_C || t == -127.0f) {
    s_ds18b20_ready = false;
    return 25.0f;
  }
  s_ds18b20_ready = true;
  return t;
}

#if ENABLE_PH_SENSOR
float read_ph_raw(void) {
  ensure_calibration_loaded();
  int raw = analogRead(PIN_PH_ANALOG);
  float V = adc_to_voltage(raw);
  float ph = ph_from_voltage(V);
  return ph + s_offset_ph;
}
static float read_ph_uncal(void) {
  int raw = analogRead(PIN_PH_ANALOG);
  float V = adc_to_voltage(raw);
  return ph_from_voltage(V);
}
#else
float read_ph_raw(void) {
  (void)s_offset_ph;
  return PH_PLACEHOLDER;
}
static float read_ph_uncal(void) {
  return PH_PLACEHOLDER;
}
#endif

float read_tds_raw(void) {
  ensure_calibration_loaded();
  int raw = analogRead(tds_adc_pin());
  float V = adc_to_voltage(raw);
  float tds_ppm = V * TDS_V_TO_PPM;
  return tds_ppm + s_offset_tds;
}

float read_temp_raw(void) {
  ensure_calibration_loaded();
  float temp_c = read_ds18b20_c();
  return temp_c + s_offset_temp;
}

float read_turbidity_raw(void) {
  ensure_calibration_loaded();
  int raw = analogRead(PIN_TURBIDITY_ANALOG);
  float V = adc_to_voltage(raw);
  float ntu = turbidity_from_voltage(V);
  return ntu + s_offset_turb;
}

static float read_tds_uncal(void) {
  int raw = analogRead(tds_adc_pin());
  float V = adc_to_voltage(raw);
  return V * TDS_V_TO_PPM;
}
static float read_temp_uncal(void) {
  return read_ds18b20_c();
}
static float read_turb_uncal(void) {
  int raw = analogRead(PIN_TURBIDITY_ANALOG);
  float V = adc_to_voltage(raw);
  return turbidity_from_voltage(V);
}

static float average_n_reads(float (*read_fn)(void)) {
  float buf[NUM_READS];
  for (int i = 0; i < NUM_READS; i++) {
    buf[i] = read_fn();
    if (i < NUM_READS - 1) delay(READ_DELAY_MS);
  }
#if SENSORS_REJECT_OUTLIERS
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

void sensors_load_calibration(void) {
  Preferences prefs;
  if (!prefs.begin(NVS_NAMESPACE, true)) return;
  s_offset_ph   = prefs.getFloat(NVS_KEY_PH_OFFSET, 0.0f);
  s_offset_tds  = prefs.getFloat(NVS_KEY_TDS_OFFSET, 0.0f);
  s_offset_temp = prefs.getFloat(NVS_KEY_TEMP_OFFSET, 0.0f);
  s_offset_turb = prefs.getFloat(NVS_KEY_TURB_OFFSET, 0.0f);
  s_ph_v_at_7   = prefs.getFloat(NVS_KEY_PH_V7, PH_V_AT_7_DEFAULT);
  s_turb_v_clear = prefs.getFloat(NVS_KEY_TURB_VCLR, TURB_V_CLEAR_DEFAULT);
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

void sensors_reset_calibration(void) {
  Preferences prefs;
  if (prefs.begin(NVS_NAMESPACE, false)) {
    prefs.putFloat(NVS_KEY_PH_V7, PH_V_AT_7_DEFAULT);
    prefs.putFloat(NVS_KEY_TURB_VCLR, TURB_V_CLEAR_DEFAULT);
    prefs.end();
  }
  s_ph_v_at_7 = PH_V_AT_7_DEFAULT;
  s_turb_v_clear = TURB_V_CLEAR_DEFAULT;
  sensors_save_calibration(0.0f, 0.0f, 0.0f, 0.0f);
  Serial.println(F("[sensors] pH + turbidity baselines reset. Send P then T in plain clear water."));
}

void sensors_calibrate_ph_neutral(void) {
#if ENABLE_PH_SENSOR
  delay(500);
  float V = read_ph_voltage();
  s_ph_v_at_7 = V;
  s_offset_ph = 0.0f;
  Preferences prefs;
  if (prefs.begin(NVS_NAMESPACE, false)) {
    prefs.putFloat(NVS_KEY_PH_V7, V);
    prefs.putFloat(NVS_KEY_PH_OFFSET, 0.0f);
    prefs.end();
  }
  float ph = ph_from_voltage(V);
  Serial.printf("[sensors] pH neutral saved: V7=%.3f V → pH %.2f in this water\n", V, ph);
  Serial.println(F("[sensors] Use pH 7 buffer for best accuracy; never send P in lemon/acid water."));
#else
  Serial.println(F("[sensors] pH sensor disabled"));
#endif
}

void sensors_calibrate_turbidity_clear(void) {
  delay(500);
  int raw = analogRead(PIN_TURBIDITY_ANALOG);
  float V = adc_to_voltage(raw);
  if (raw < 50) {
    Serial.printf("[sensors] ERROR: turbidity raw=%d — fix D34 wiring before T calibration\n", raw);
    return;
  }
  s_turb_v_clear = V;
  s_offset_turb = 0.0f;
  Preferences prefs;
  if (prefs.begin(NVS_NAMESPACE, false)) {
    prefs.putFloat(NVS_KEY_TURB_VCLR, V);
    prefs.putFloat(NVS_KEY_TURB_OFFSET, 0.0f);
    prefs.end();
  }
  Serial.printf("[sensors] Turbidity clear saved: V=%.3f V → 0 NTU in this water\n", V);
  Serial.println(F("[sensors] Cloudy/murky water should read >0; clear lemon juice may stay low (dissolved, not particles)."));
}

void sensors_print_reading(const char* label) {
  SensorReading_t r = sensors_read_averaged();
  Serial.print(label ? label : "[sensors]");
#if ENABLE_PH_SENSOR
  int phRaw = analogRead(PIN_PH_ANALOG);
  float phV = adc_to_voltage(phRaw);
  Serial.printf(" pH=%.2f (raw=%d V=%.3f)", r.ph, phRaw, phV);
#else
  Serial.print(F(" pH=")); Serial.print(r.ph);
#endif
  Serial.print(F(" TDS=")); Serial.print(r.tds);
  Serial.print(F(" T=")); Serial.print(r.temp);
  int turbRaw = analogRead(PIN_TURBIDITY_ANALOG);
  float turbV = adc_to_voltage(turbRaw);
  Serial.printf(" Turb=%.1f (raw=%d V=%.3f)", r.turbidity, turbRaw, turbV);
  Serial.println();
}
