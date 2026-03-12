"""
Phase 5.8 — Sensor range bounds for out-of-range detection on upload.

If any sensor value is outside these bounds, an Alert (type=out_of_range) and SystemLog are created.
"""
# (low, high) inclusive bounds for acceptable sensor values
SENSOR_RANGES = {
    "ph": (0.0, 14.0),
    "tds": (0.0, 20000.0),
    "temperature": (-10.0, 60.0),
    "turbidity": (0.0, 500.0),
}
