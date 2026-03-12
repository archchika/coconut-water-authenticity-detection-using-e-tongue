# E-Tongue Sensor Fusion (Phase 2)

Signal-processing layer: raw sensor stream → clean feature vector for ML. Runs on Raspberry Pi or local PC (factory offline).

## Phase 2.1 — Input interface and config

- **Config:** `config.yaml` — input source (serial / tcp / http), pipeline params (moving_average_window, baseline, filter).
- **Input interface:** `input_sources.py` — `parse_esp32_json()`, `get_input_source(config)`, `SerialInput` (implemented), `TCPInput` / `HTTPInput` (stubbed for later).
- **Config loader:** `config_loader.py` — `load_config()`, `get_input_config()`, `get_pipeline_config()`.

### Config schema

- **input.source:** `serial` | `tcp` | `http`
- **input.serial:** port, baud, timeout_sec
- **input.tcp:** host, port (listen)
- **input.http:** host, port, path (POST endpoint)
- **pipeline.moving_average_window:** int (e.g. 5–10)
- **pipeline.baseline:** ph, tds, temperature, turbidity (floats)
- **pipeline.filter:** type (median | lowpass), window, alpha

### ESP32 JSON format (input)

One JSON object per line, as sent by firmware:

```json
{"timestamp_ms":12345,"pH":5.2,"tds":100,"temperature":25.0,"turbidity":50.0,"status":"unknown"}
```

### Usage example

```python
from pathlib import Path
from config_loader import load_config, get_input_config
from input_sources import get_input_source, parse_esp32_json

config = load_config(Path("config.yaml"))
source = get_input_source(config)
# source.open()  # for SerialInput
# sample = source.get_next_sample()  # dict with pH, tds, temperature, turbidity, timestamp_ms, status
```

Edit `config.yaml` and set **input.serial.port** to your ESP32 serial port (e.g. `COM3` on Windows, `/dev/ttyUSB0` on Linux/RPi).

## Phase 2.2 — Noise filtering per channel

- **filters.py:** `LowPassFilter(alpha)` (exponential moving average), `MedianFilter(window)` (sliding-window median), `PerChannelFilter(pipeline_config)` (one filter per channel).
- **Config:** `pipeline.filter.type` (median | lowpass), `window`, `alpha`; optional `pipeline.filter.channels.<ph|tds|temperature|turbidity>` with per-channel type/window/alpha.
- **Usage:** `f = PerChannelFilter(get_pipeline_config(config)); filtered = f.update(sample)` — returns dict with filtered pH, tds, temperature, turbidity.

## Phase 2.3 — Moving average smoothing

- **smoothing.py:** `RollingMovingAverage(window)` (single-channel rolling mean), `PerChannelMovingAverage(pipeline_config)` (one rolling mean per channel).
- **Config:** `pipeline.moving_average_window` (default 5); optional `pipeline.moving_average_windows.ph`, `.tds`, `.temperature`, `.turbidity` for per-channel window size.
- **Usage:** `s = PerChannelMovingAverage(get_pipeline_config(config)); smoothed = s.update(sample)` — returns dict with smoothed pH, tds, temperature, turbidity.

## Phase 2.4 — Baseline normalization

- **baseline.py:** `BaselineNormalizer(pipeline_config)` loads baseline from `pipeline.baseline` (ph, tds, temperature, turbidity) and subtracts it per channel: `normalized = value - baseline`.
- **Config:** `pipeline.baseline` in config.yaml (already present); values are subtracted from smoothed/filtered samples.
- **Usage:** `b = BaselineNormalizer(get_pipeline_config(config)); normalized = b.update(sample)` — returns dict with baseline-subtracted values; `b.get_baseline()` returns the loaded baseline.

## Phase 2.5 — Feature vector assembly

- **features.py:** Fixed order `[pH, tds, temperature, turbidity]`; optional derived features (e.g. `ph_tds`, `turb_per_temp`, `tds_per_ph`) appended when listed in `pipeline.derived_features`.
- **`sample_to_array(sample, include_derived=None)`** — Returns 1D numpy array (float64). **`get_feature_vector(sample, pipeline_config=None)`** — Returns `(array, metadata)` for Phase 3; metadata has `timestamp_ms`, `status`. **`feature_names(pipeline_config)`** — Names in same order as array.
- **Config:** Optional `pipeline.derived_features: [ph_tds, turb_per_temp]` in config.yaml.

## Phase 2.6 — Structured output and API

- **output.py:** **`to_structured_output(sample)`** — Returns dict `{ "pH", "tds", "temp", "turbidity", "timestamp": ISO8601, "status" }` for ML/API. **`timestamp_ms_to_iso8601(ms)`** — Converts ESP32 ms to UTC ISO8601. **`log_raw(config, sample)`** and **`log_fused(config, structured)`** — When `config.log.raw` / `config.log.fused` are true, log at DEBUG for calibration/debug.
- **Phase 3 API:** **`get_feature_vector(sample, pipeline_config)`** in `features.py` returns `(array, metadata)`; `metadata` includes `timestamp` (ISO8601), `timestamp_ms`, `status`.

## Phase 2.7 — Pipeline integration and tests

- **pipeline.py:** **`FusionPipeline(config)`** — Single entry: **`update(raw_sample)`** runs Raw → Filter → Moving avg → Baseline, then returns **`(structured_output, feature_array, metadata)`**. **`reset()`** clears filter and smoother state.
- **Tests:** `sensor_fusion/tests/test_pipeline.py` — pytest tests: single/multiple samples through pipeline, feature order, structured output keys, reset. Run from repo root: **`pytest sensor_fusion/tests/`** (or `cd sensor_fusion && pytest tests/`).

## Sub-phase status

| Sub-Phase | Description | Status |
|-----------|-------------|--------|
| 2.1 | Input interface and config | Done |
| 2.2 | Noise filtering per channel | Done |
| 2.3 | Moving average smoothing | Done |
| 2.4 | Baseline normalization | Done |
| 2.5 | Feature vector assembly | Done |
| 2.6 | Structured output and API | Done |
| 2.7 | Pipeline integration and tests | Done |
