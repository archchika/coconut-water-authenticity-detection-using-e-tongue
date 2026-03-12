/**
 * Serial (debug) and WiFi HTTP POST to local ML server
 */
#ifndef TRANSPORT_H
#define TRANSPORT_H

#include <Arduino.h>
#include "sensors.h"

// Print reading to Serial (JSON line)
void transport_serial_log(const SensorReading_t* r, const char* status);

// POST reading to ML server. status = "authentic" | "adulterated" | "unknown"
// Returns true if sent successfully (or no WiFi configured)
bool transport_post_reading(const SensorReading_t* r, const char* status);

// Optional: WiFi connect (call from setup)
void transport_wifi_connect(void);
bool transport_wifi_connected(void);

#endif // TRANSPORT_H
