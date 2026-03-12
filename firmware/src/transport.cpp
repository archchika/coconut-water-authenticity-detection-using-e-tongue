/**
 * E-Tongue ESP32 — Serial JSON log and WiFi HTTP POST (Phase 1.6, Phase 5.2)
 * Phase 5.2: Retry with exponential backoff; log failures locally.
 */
#include "transport.h"
#include "config.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <string.h>

#define JSON_BUF_SIZE 320
#define URL_BUF_SIZE  128

static void build_json_body(const SensorReading_t* r, const char* status, char* buf, size_t size) {
  unsigned long ts = millis();
  (void)snprintf(buf, size,
    "{\"timestamp_ms\":%lu,\"pH\":%.2f,\"tds\":%.1f,\"temperature\":%.1f,\"turbidity\":%.1f,\"status\":\"%s\"}",
    ts, r->ph, r->tds, r->temp, r->turbidity, status ? status : "unknown");
}

void transport_serial_log(const SensorReading_t* r, const char* status) {
  if (!r) return;
  char buf[JSON_BUF_SIZE];
  build_json_body(r, status ? status : "unknown", buf, sizeof(buf));
  Serial.println(buf);
}

void transport_wifi_connect(void) {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && (unsigned long)(millis() - t0) < (unsigned long)WIFI_CONNECT_TIMEOUT_MS) {
    delay(200);
  }
}

bool transport_wifi_connected(void) {
  return WiFi.status() == WL_CONNECTED;
}

bool transport_post_reading(const SensorReading_t* r, const char* status) {
  if (!r) return false;

  transport_wifi_connect();
  if (!transport_wifi_connected()) {
    Serial.println("[transport] POST skipped: WiFi not connected");
    return false;
  }

  char body[JSON_BUF_SIZE];
  build_json_body(r, status ? status : "unknown", body, sizeof(body));

  char url[URL_BUF_SIZE];
  (void)snprintf(url, sizeof(url), "http://%s:%u%s", ML_SERVER_HOST, (unsigned)ML_SERVER_PORT, ML_POST_PATH);

  int last_code = -1;
  for (int attempt = 0; attempt < TRANSPORT_POST_RETRIES; attempt++) {
    HTTPClient http;
    if (!http.begin(url)) {
      http.end();
      Serial.printf("[transport] POST attempt %d: http.begin failed\n", attempt + 1);
      if (attempt < TRANSPORT_POST_RETRIES - 1) {
        unsigned long backoff_ms = (unsigned long)TRANSPORT_POST_RETRY_DELAY_MS * (1u << (unsigned)attempt);
        delay(backoff_ms);
      }
      continue;
    }
    http.addHeader("Content-Type", "application/json");
    int code = http.POST((const uint8_t*)body, strlen(body));
    last_code = code;
    http.end();
    if (code == HTTP_CODE_OK || code == HTTP_CODE_CREATED || code == HTTP_CODE_ACCEPTED) {
      return true;
    }
    Serial.printf("[transport] POST attempt %d failed: HTTP %d\n", attempt + 1, code);
    if (attempt < TRANSPORT_POST_RETRIES - 1) {
      unsigned long backoff_ms = (unsigned long)TRANSPORT_POST_RETRY_DELAY_MS * (1u << (unsigned)attempt);
      delay(backoff_ms);
    }
  }
  Serial.printf("[transport] POST failed after %d retries (last HTTP %d)\n", TRANSPORT_POST_RETRIES, last_code);
  return false;
}
