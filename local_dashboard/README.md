# E-Tongue Local Monitoring Dashboard (Phase 4)

Streamlit app for real-time sensor and (when available) ML output. Runs on Raspberry Pi or local PC (factory offline).

## Phase 4.1 — Dashboard project and data source

- **App structure:** `app.py` (Streamlit entry), `config_loader.py`, `data_source.py`, `config.yaml`.
- **Data source:** Poll an HTTP URL for the latest reading (JSON). Configure in `config.yaml`:
  - **`data_source.url`** — e.g. `http://127.0.0.1:5000/api/current` (local server that serves last reading from ESP32 or fusion).
  - **`data_source.refresh_interval_sec`** — Poll interval (e.g. 3 s).
  - **`data_source.timeout_sec`** — Request timeout.
- **Fetch:** `fetch_latest_reading(url, timeout_sec)` in `data_source.py` — GET url, parse JSON; returns dict or None. Expected keys: pH, tds, temperature, turbidity, timestamp_ms, status (optional: predicted_sugar, predicted_citric, predicted_ascorbic, authenticity).

### Run

```bash
cd local_dashboard
pip install -r requirements.txt
streamlit run app.py
```

Set `config.yaml` **data_source.url** to your local server URL. If no server is running, the dashboard shows "No data yet" and the expected JSON shape.

### Phase 4.2 — Real-time live graphs

- **components/charts.py:** **`render_live_charts(readings)`** — Builds two Plotly figures: (1) pH over time (timestamp_ms); (2) Predicted Sugar %, Citric %, Ascorbic % over time if keys `predicted_sugar`, `predicted_citric`, `predicted_ascorbic` are present in any reading. **`append_reading(readings, new_reading, max_points, max_seconds)`** — Appends one reading and trims to last N points / last N seconds.
- **Config:** **`graphs.max_points`** (default 100), **`graphs.max_seconds`** (default 300 = 5 min).
- **App:** Session state holds a rolling buffer of readings; each run fetches latest, appends, trims, and renders the two charts. Latest reading (raw JSON) is in an expander.

### Phase 4.3 — Final averaged reading display

- **Final averaged reading** section at the top of the main area: four **st.metric** cards for pH, TDS (ppm), Temperature (°C), Turbidity (latest value from data source). If the reading includes **predicted_sugar**, **predicted_citric**, **predicted_ascorbic**, a second row of three metrics shows them; otherwise "—". Timestamp (ms) shown as caption. If no reading, an info message is shown.

### Phase 4.4 — Red alert box and alarm indicator

- **Alert status** section directly under the final averaged reading. Uses the latest `reading` dict to determine if an alert is active:
  - If `status` is `"threshold_alert"` (from firmware threshold checks), shows a red **st.error** panel: "Sensor thresholds exceeded – possible abnormal sample. Check readings and cleaning cycle."
  - If `status` is `"adulterated"` or `authenticity` is `"Adulterated"` (from ML pipeline), shows a red **st.error** panel: "Sample classified as ADULTERATED by ML pipeline."
  - Otherwise, shows a green **st.success** panel indicating values are within safe / natural ranges.
- **Sidebar alarm indicator** mirrors this state:
  - Red **Alarm: ACTIVE** when an alert is active.
  - Green **Alarm: normal** when there is no alert.
  - Grey **Alarm: waiting for first reading** before any data has arrived.

### Phase 4.5 — Historical mini log

- **Historical mini log** section: scrollable **st.dataframe** showing the last 50 readings from the session buffer.
- Columns: **Timestamp (ms)**, **pH**, **TDS**, **Temp (°C)**, **Turbidity**, **Status**, **Authenticity** (timestamp and authenticity decision as per phase spec).
- **components/charts.py:** **`last_n_readings(readings, limit=50)`** — returns the last `limit` readings in chronological order for the mini log.

### Phase 4.6 — System state display and auto-refresh

- **System state** section at the top of the main area: **st.metric("Current state", label)**. Label is one of: **Idle**, **Detecting**, **Read complete**, **Cleaning**, **Rinsing**, **Drying**, **Stabilising**, **Ready**, **Calibration**. Uses **system_state** or **state** from the latest reading when provided by gateway/firmware; otherwise shows "Idle / Waiting" (no data) or "Ready" (data present). Same label is shown in the sidebar as **System state**.
- **Auto-refresh:** **streamlit-autorefresh** runs a timer that triggers a full app rerun every **refresh_interval_sec** (config, typically 2–5 s). Each rerun fetches the latest reading from the data source and updates graphs, metrics, and state. Sidebar shows "Auto-refresh: ON, every X s".

### Sub-phase status

| Sub-Phase | Description | Status |
|-----------|-------------|--------|
| 4.1 | Dashboard project and data source | Done |
| 4.2 | Real-time live graphs | Done |
| 4.3 | Final averaged reading display | Done |
| 4.4 | Red alert box and alarm indicator | Done |
| 4.5 | Historical mini log | Done |
| 4.6 | System state display and auto-refresh | Done |
| 4.7 | Cleaning automation — detection complete and trigger | Done |
| 4.8 | Cleaning automation — rinse and dryer | Done |
| 4.9 | Cleaning automation — stabilisation and reset | Done |
| 4.10 | State machine alignment and documentation | Done |

### Phase 4.7 — Cleaning automation: detection complete and trigger

- **Logic (firmware):** When the 3× averaged read is done (**READ_COMPLETE**), the device logs and HTTP POSTs the reading to the local ML server (reading done; ML receives data). It then transitions to **CLEANING** (no wait for ML response in current design; optional gateway can wait for ML result before signalling).
- **Move-to-station trigger:** On entering **CLEANING**, the firmware calls **`cleaning_move_to_station()`** (Phase 4.7): pulses **PIN_ROBOT_MOVE_STATION** (configurable, e.g. GPIO 33) for **MOVE_TO_STATION_PULSE_MS**, then waits **MOVE_TO_STATION_WAIT_MS** for the robotic arm to reach the cleaning station, then turns the rinse relay ON and transitions to **RINSING**.
- **Config (firmware `config.h`):** **USE_ROBOT_MOVE_STATION** (0 = no-op, 1 = use pin), **PIN_ROBOT_MOVE_STATION**, **MOVE_TO_STATION_PULSE_MS**, **MOVE_TO_STATION_WAIT_MS**. See **firmware/STATE_DIAGRAM.md** for the full transition table.

### Phase 4.8 — Cleaning automation: rinse and dryer

- **Rinse:** On entering **RINSING**, the rinse relay (distilled water pump) is already ON. The state machine waits **RINSE_DURATION_MS** (config.h, default 10 s). When the duration elapses, it calls **cleaning_rinse_off()**, then **cleaning_dryer_on()**, and transitions to **DRYING**.
- **Dryer:** In **DRYING**, the dryer relay stays ON for **DRYER_DURATION_MS** (config.h, default 30 s). When the duration elapses, it calls **cleaning_dryer_off()**, starts the stabilisation phase (**stabilise_start()**), and transitions to **STABILIZE** (Phase 4.9).
- **Config:** **RINSE_DURATION_MS**, **DRYER_DURATION_MS** in **firmware/include/config.h**.

### Phase 4.9 — Cleaning automation: stabilisation and reset

- **Wait for pH baseline:** In **STABILIZE**, the firmware calls **stabilise_tick()** every loop. pH is read at **STABILIZE_INTERVAL_MS** (e.g. 1 s). When pH is within **PH_BASELINE_MIN**..**PH_BASELINE_MAX** (e.g. 6.8–7.2), a consecutive counter increments; otherwise it resets to 0. When the counter reaches **STABILIZE_READINGS** (M consecutive samples over N seconds), **stabilise_is_ready()** is true and the state machine transitions to **READY**. If **STABILIZE_TIMEOUT_MS** elapses before that, **stabilise_timed_out()** is true and the machine still goes to **READY** (allows next cycle without blocking indefinitely).
- **Reset flags; set state to READY:** The transition **STABILIZE → READY** is the “set state to READY”. In **READY**, the firmware clears the alert (**alert_buzzer_off()**), resets the stabilisation state (**stabilise_reset()**), then transitions to **IDLE**.
- **Allow next DETECTING cycle:** From **IDLE**, a new cycle can be started (Serial `G` or **state_machine_request_start()**), leading to **DETECTING**.
- **Config (firmware `config.h`):** **PH_BASELINE_MIN**, **PH_BASELINE_MAX**, **STABILIZE_READINGS** (M), **STABILIZE_INTERVAL_MS**, **STABILIZE_TIMEOUT_MS**.

### Phase 4.10 — State machine alignment and documentation

- **State names:** Firmware state names (IDLE, DETECTING, READ_COMPLETE, CLEANING, RINSING, DRYING, STABILIZE, READY, CALIBRATION) are the canonical set. The gateway/ESP32 should send one of these as **system_state** or **state** in the JSON reading.
- **Shared module:** **state_names.py** defines the same constants and **STATE_DISPLAY_LABELS**, and **state_to_display_label(raw_state, has_reading)** for the dashboard. Use this module in any Python automation that needs to read or emit state.
- **Documentation:** **STATE_ALIGNMENT.md** lists the state-name table (firmware ↔ JSON ↔ display label) and points to **firmware/STATE_DIAGRAM.md** as the source of truth for transitions. **STATE_DIAGRAM.md** has been updated with a Phase 4.10 alignment section.
- **Dashboard:** System state display (Phase 4.6) now uses **state_names.state_to_display_label()** so labels stay aligned with firmware.
