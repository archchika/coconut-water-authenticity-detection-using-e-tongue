"""
E-Tongue Sensor Fusion — Input interface (Phase 2.1)
Define input source (Serial / TCP / HTTP from ESP32); parse ESP32 JSON format.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ESP32 JSON keys (from firmware transport.cpp)
KEY_TIMESTAMP_MS = "timestamp_ms"
KEY_PH = "pH"
KEY_TDS = "tds"
KEY_TEMPERATURE = "temperature"
KEY_TURBIDITY = "turbidity"
KEY_STATUS = "status"


def parse_esp32_json(line: str) -> dict[str, Any] | None:
    """
    Parse one line of JSON from ESP32 (Serial or HTTP body).
    Expected keys: timestamp_ms, pH, tds, temperature, turbidity, status.
    Returns dict with float values for pH, tds, temperature, turbidity; int for timestamp_ms; str for status.
    Returns None if parse fails or required keys missing.
    """
    line = line.strip()
    if not line:
        return None
    try:
        data = json.loads(line)
    except json.JSONDecodeError as e:
        logger.debug("Invalid JSON from ESP32: %s", e)
        return None
    if not isinstance(data, dict):
        return None
    required = (KEY_PH, KEY_TDS, KEY_TEMPERATURE, KEY_TURBIDITY)
    for k in required:
        if k not in data:
            logger.debug("Missing key in ESP32 payload: %s", k)
            return None
    try:
        return {
            KEY_TIMESTAMP_MS: int(data.get(KEY_TIMESTAMP_MS, 0)),
            KEY_PH: float(data[KEY_PH]),
            KEY_TDS: float(data[KEY_TDS]),
            KEY_TEMPERATURE: float(data[KEY_TEMPERATURE]),
            KEY_TURBIDITY: float(data[KEY_TURBIDITY]),
            KEY_STATUS: str(data.get(KEY_STATUS, "unknown")),
        }
    except (TypeError, ValueError):
        return None


def get_next_sample_serial(port: str, baud: int = 115200, timeout_sec: float = 1.0) -> dict[str, Any] | None:
    """
    Read one line from serial port and parse as ESP32 JSON.
    Blocks until a valid sample is read or timeout. Requires pyserial.
    """
    try:
        import serial
    except ImportError:
        raise ImportError("pyserial required for serial input: pip install pyserial")
    with serial.Serial(port=port, baudrate=baud, timeout=timeout_sec) as ser:
        while True:
            line = ser.readline()
            if not line:
                return None
            try:
                text = line.decode("utf-8").strip()
            except UnicodeDecodeError:
                continue
            sample = parse_esp32_json(text)
            if sample is not None:
                return sample
    return None


def get_input_source(config: dict[str, Any]):
    """
    Return an input source object from config.
    Config must have input.source and input.<source> params.
    Supported: serial (returns a wrapper that yields samples); tcp/http raise NotImplementedError for now.
    """
    inp = config.get("input") or {}
    source = (inp.get("source") or "serial").lower()
    if source == "serial":
        ser_cfg = inp.get("serial") or {}
        port = ser_cfg.get("port", "COM3")
        baud = int(ser_cfg.get("baud", 115200))
        timeout = float(ser_cfg.get("timeout_sec", 1.0))
        return SerialInput(port=port, baud=baud, timeout_sec=timeout)
    if source == "tcp":
        tcp_cfg = inp.get("tcp") or {}
        return TCPInput(host=tcp_cfg.get("host", "0.0.0.0"), port=int(tcp_cfg.get("port", 9000)))
    if source == "http":
        http_cfg = inp.get("http") or {}
        return HTTPInput(
            host=http_cfg.get("host", "0.0.0.0"),
            port=int(http_cfg.get("port", 8000)),
            path=http_cfg.get("path", "/api/reading"),
        )
    raise ValueError(f"Unknown input source: {source}")


class SerialInput:
    """Input source: read JSON lines from serial port (ESP32 or bridge)."""

    def __init__(self, port: str, baud: int = 115200, timeout_sec: float = 1.0):
        self.port = port
        self.baud = baud
        self.timeout_sec = timeout_sec
        self._ser = None

    def open(self):
        try:
            import serial
        except ImportError:
            raise ImportError("pyserial required: pip install pyserial")
        self._ser = serial.Serial(port=self.port, baudrate=self.baud, timeout=self.timeout_sec)

    def close(self):
        if self._ser is not None:
            self._ser.close()
            self._ser = None

    def get_next_sample(self) -> dict[str, Any] | None:
        """Block until one valid ESP32 JSON line is read; return parsed dict or None on timeout/close."""
        if self._ser is None:
            self.open()
        while True:
            line = self._ser.readline()
            if not line:
                return None
            try:
                text = line.decode("utf-8").strip()
            except UnicodeDecodeError:
                continue
            sample = parse_esp32_json(text)
            if sample is not None:
                return sample


class TCPInput:
    """Input source: listen on TCP for incoming JSON lines (ESP32 or bridge). Not implemented in 2.1."""

    def __init__(self, host: str = "0.0.0.0", port: int = 9000):
        self.host = host
        self.port = port

    def get_next_sample(self) -> dict[str, Any] | None:
        raise NotImplementedError("TCP input will be implemented in a later sub-phase; use config input.source: serial for now.")


class HTTPInput:
    """Input source: run HTTP server; ESP32 POSTs JSON; get_next_sample() returns from queue. Not implemented in 2.1."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000, path: str = "/api/reading"):
        self.host = host
        self.port = port
        self.path = path

    def get_next_sample(self) -> dict[str, Any] | None:
        raise NotImplementedError("HTTP input will be implemented in a later sub-phase; use config input.source: serial for now.")
