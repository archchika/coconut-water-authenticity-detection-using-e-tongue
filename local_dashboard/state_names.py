"""
Phase 4.10 — State machine alignment: canonical state names shared with firmware.

Firmware (state_machine.h) uses enum State_t; these string constants match
the names used in STATE_DIAGRAM.md and should be sent by gateway/ESP32
as "system_state" or "state" in the JSON reading.

Source of truth for transitions: firmware/STATE_DIAGRAM.md
"""

# Canonical state names (match firmware state_name() / S_NAMES[])
STATE_IDLE = "IDLE"
STATE_DETECTING = "DETECTING"
STATE_READ_COMPLETE = "READ_COMPLETE"
STATE_CLEANING = "CLEANING"
STATE_RINSING = "RINSING"
STATE_DRYING = "DRYING"
STATE_STABILIZE = "STABILIZE"
STATE_READY = "READY"
STATE_CALIBRATION = "CALIBRATION"

ALL_STATES = (
    STATE_IDLE,
    STATE_DETECTING,
    STATE_READ_COMPLETE,
    STATE_CLEANING,
    STATE_RINSING,
    STATE_DRYING,
    STATE_STABILIZE,
    STATE_READY,
    STATE_CALIBRATION,
)

# Display labels for UI (Phase 4.6 / 4.10)
STATE_DISPLAY_LABELS = {
    STATE_IDLE: "Idle",
    STATE_DETECTING: "Detecting",
    STATE_READ_COMPLETE: "Read complete",
    STATE_CLEANING: "Cleaning",
    STATE_RINSING: "Rinsing",
    STATE_DRYING: "Drying",
    STATE_STABILIZE: "Stabilising",
    STATE_READY: "Ready",
    STATE_CALIBRATION: "Calibration",
}


def state_to_display_label(raw_state: str | None, has_reading: bool = True) -> str:
    """
    Map firmware/gateway state string to display label (Phase 4.10 alignment).
    raw_state: value of "system_state" or "state" from reading (case-insensitive).
    has_reading: True if a reading was received (so "no state" can show as "Ready").
    Returns human-readable label; "Ready" if unknown/empty when has_reading; "Idle / Waiting" if no reading.
    """
    if raw_state is None or not str(raw_state).strip():
        return "Ready" if has_reading else "Idle / Waiting"
    key = str(raw_state).strip().upper()
    return STATE_DISPLAY_LABELS.get(key, "Ready")
