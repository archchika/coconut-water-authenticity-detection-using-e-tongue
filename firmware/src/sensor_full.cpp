/**
 * sensor_full.cpp — Periodic full sensor read (pH + TDS + temp + turbidity).
 *
 * Every SENSOR_FULL_INTERVAL_MS (default 10 s):
 *   1. One single read per sensor (not 3× average)
 *   2. One combined snapshot
 *   3. One WiFi POST to /api/esp32-reading/
 *
 * Serial: F = read+send now | S = print detection status
 */
#include "sensor_full.h"
#include "config.h"
#include "transport.h"
#include "alerts.h"

static unsigned long s_last_cycle_ms = 0;
static SensorFullStatus_t s_status = { 0 };

static int tds_pin_for_detect(void) {
#if USE_TDS_PIN_ALT
  return PIN_TDS_ANALOG_ALT;
#else
  return PIN_TDS_ANALOG;
#endif
}

static bool analog_sensor_detected(int pin, int min_raw) {
  int raw = analogRead(pin);
  return raw > min_raw;
}

static SensorReading_t sensor_full_read_once(void) {
  SensorReading_t r;
  r.ph        = read_ph_raw();
  delay(50);
  r.tds       = read_tds_raw();
  delay(50);
  r.temp      = read_temp_raw();
  delay(50);
  r.turbidity = read_turbidity_raw();
  return r;
}

void sensor_full_init(void) {
  s_last_cycle_ms = millis();

  s_status.ph_detected = false;
  s_status.tds_detected = false;
  s_status.temp_detected = false;
  s_status.turb_detected = false;

#if ENABLE_PH_SENSOR
  s_status.ph_detected = analog_sensor_detected(PIN_PH_ANALOG, 50);
  Serial.printf("[sensor_full] pH GPIO%d %s\n", PIN_PH_ANALOG,
                s_status.ph_detected ? "detected" : "NOT detected (check wiring)");
#else
  Serial.println(F("[sensor_full] pH disabled in config.h (ENABLE_PH_SENSOR=0)"));
#endif

  s_status.tds_detected = analog_sensor_detected(tds_pin_for_detect(), 50);
  Serial.printf("[sensor_full] TDS GPIO%d (D%d) %s\n", tds_pin_for_detect(), tds_pin_for_detect(),
                s_status.tds_detected ? "detected" : "NOT detected — wire to D32");

  SensorReading_t probe = sensor_full_read_once();
  s_status.temp_detected = (probe.temp > -100.0f && probe.temp < 125.0f);
  Serial.printf("[sensor_full] Temperature DS18B20 D4 %s (%.1f C)\n",
                s_status.temp_detected ? "detected" : "NOT detected",
                probe.temp);

  s_status.turb_detected = analog_sensor_detected(PIN_TURBIDITY_ANALOG, 50);
  Serial.printf("[sensor_full] Turbidity GPIO%d (D34) %s — do NOT use D35 (pH uses it)\n",
                PIN_TURBIDITY_ANALOG,
                s_status.turb_detected ? "detected" : "NOT detected");

  Serial.printf("[sensor_full] Cycle every %lu ms — one reading each → one POST\n",
                (unsigned long)SENSOR_FULL_INTERVAL_MS);
}

void sensor_full_print_status(void) {
  Serial.println(F("--- sensor_full status ---"));
#if ENABLE_PH_SENSOR
  Serial.printf("  pH:        %s\n", s_status.ph_detected ? "OK" : "MISSING");
#else
  Serial.println(F("  pH:        disabled"));
#endif
  Serial.printf("  TDS:       %s\n", s_status.tds_detected ? "OK" : "MISSING");
  Serial.printf("  Temp:      %s\n", s_status.temp_detected ? "OK" : "MISSING");
  Serial.printf("  Turbidity: %s\n", s_status.turb_detected ? "OK" : "MISSING");
  Serial.printf("  Last: pH=%.2f TDS=%.1f T=%.1f Turb=%.1f\n",
                s_status.ph, s_status.tds, s_status.temp, s_status.turbidity);
}

SensorFullStatus_t sensor_full_get_status(void) {
  return s_status;
}

void sensor_full_read_and_send(void) {
  SensorReading_t r = sensor_full_read_once();

  s_status.ph = r.ph;
  s_status.tds = r.tds;
  s_status.temp = r.temp;
  s_status.turbidity = r.turbidity;

  Serial.print(F("[sensor_full] "));
  Serial.print(F("pH=")); Serial.print(r.ph, 2);
#if ENABLE_PH_SENSOR
  int phRaw = analogRead(PIN_PH_ANALOG);
  Serial.printf("(V=%.3f)", (phRaw / ADC_RESOLUTION) * ADC_VREF);
#endif
  Serial.print(F(" TDS=")); Serial.print(r.tds, 1);
  Serial.print(F(" T=")); Serial.print(r.temp, 1);
  int turbRaw = analogRead(PIN_TURBIDITY_ANALOG);
  float turbV = (turbRaw / ADC_RESOLUTION) * ADC_VREF;
  Serial.printf(" Turb=%.1f(raw=%d V=%.3f)", r.turbidity, turbRaw, turbV);
  Serial.println();

  const char* row_status = alerts_check_thresholds(&r) ? "threshold_alert" : "unknown";
  transport_serial_log(&r, row_status);

  if (transport_post_reading(&r, row_status)) {
    Serial.println(F("[sensor_full] Sent 1 reading to backend"));
  } else {
    Serial.println(F("[sensor_full] POST failed — check WiFi + backend run-lan.bat"));
  }
}

void sensor_full_tick(void) {
  unsigned long now = millis();
  if ((unsigned long)(now - s_last_cycle_ms) < (unsigned long)SENSOR_FULL_INTERVAL_MS)
    return;

  s_last_cycle_ms = now;
  Serial.println(F("[sensor_full] 10s cycle — reading all sensors..."));
  sensor_full_read_and_send();
}
