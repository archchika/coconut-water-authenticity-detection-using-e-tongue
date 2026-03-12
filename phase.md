# Six-Phase Development Plan: IoT-Based E-Tongue System for Coconut Water Authenticity Detection

**Project:** Design and Development of an IoT-Based E-Tongue System for Coconut Water Authenticity Detection Using Sensor Fusion, Regression Modeling, Robotic Integration, and Web Transparency Platform.

**Repository:** https://github.com/archchika/coconut-water-authenticity-detection-using-e-tongue

**Constraint:** Do not update this file after creation; use as stable reference. All implementation follows this plan.

---

## Phase 1 — Foundation & Hardware Layer

**Objective:** Establish ESP32 firmware, sensor acquisition, state machine, cleaning automation logic, and local alerting. System must operate offline in factory.

### Sub-Phases

| Sub-Phase | Title | Work |
|-----------|--------|------|
| **1.1** | Project setup and pin configuration | Create firmware project (PlatformIO/Arduino), `config.h` with pin mapping, ADC resolution, timing constants; folder structure. |
| **1.2** | Sensor drivers and single-read logic | Implement one-shot read for pH, TDS, temperature, turbidity (ADC → physical units); apply calibration offsets from NVS. |
| **1.3** | 3-time averaging and timing | Per sensor: take 3 readings with configurable delay; compute mean; optional outlier rejection. |
| **1.4** | State machine implementation | Implement all states (IDLE, DETECTING, READ_COMPLETE, CLEANING, RINSING, DRYING, STABILIZE, READY) and transitions; central tick function. |
| **1.5** | Threshold detection and buzzer alert | Compare readings to safe ranges; trigger buzzer on anomaly; optional adulteration alert from ML result. |
| **1.6** | Serial and WiFi transport | Serial: JSON log of readings; WiFi: connect, HTTP POST to local ML server with retry. |
| **1.7** | Cleaning station automation | GPIO control for rinse and dryer relays; sequence: move → rinse (duration) → dryer (duration). |
| **1.8** | Sensor reset and stabilisation | After drying: poll pH until within baseline range for N consecutive samples; then allow READY. |
| **1.9** | Calibration routine and NVS storage | Mode to record known samples (e.g. buffer solutions); compute and store offsets in NVS/EEPROM; load on boot. |
| **1.10** | Integration, testing, and documentation | Wire main loop to state machine and sensors; state diagram, pin mapping, and calibration procedure docs. |

### Deliverables (Phase 1)

| Item | Description |
|------|-------------|
| ESP32 firmware | Main loop, sensor drivers, 3-time averaging, threshold checks |
| State machine | States: `IDLE` → `DETECTING` → `READ_COMPLETE` → `CLEANING` → `RINSING` → `DRYING` → `STABILIZE` → `READY` |
| Sensor reading code | pH, TDS, temperature, turbidity with timing delays and calibration routine |
| 3-time averaging | Per-sensor: take 3 readings with configurable delay; output mean (reject outliers optional) |
| Threshold detection | Compare readings to safe/alert thresholds; trigger buzzer on anomaly |
| Buzzer alert logic | On-board buzzer for local alarm when reading out of range or adulteration suspected |
| Serial + WiFi transmission | Serial for debug; WiFi for HTTP POST to local ML server / Raspberry Pi |
| Cleaning station automation | Trigger relay/GPIO for: distilled water pump, dryer; wait for stabilisation |
| Dryer control | GPIO/timer for dryer ON duration; configurable in firmware |
| Sensor reset & stabilisation | After cleaning: poll pH until baseline (e.g. 6.8–7.2) stable for N seconds |
| Calibration routine | Mode to run calibration: record known samples (e.g. buffer solutions) and store offsets in NVS/EEPROM |

### State Machine Design (Summary)

```
[IDLE] -- start_cmd --> [DETECTING]
[DETECTING] -- 3x read done --> [READ_COMPLETE]
[READ_COMPLETE] -- send to ML --> (await response) --> [CLEANING]
[CLEANING] -- move to station --> [RINSING]
[RINSING] -- rinse_done --> [DRYING]
[DRYING] -- dryer_timeout --> [STABILIZE]
[STABILIZE] -- pH in range for N sec --> [READY]
[READY] -- reset_flags --> [IDLE]
```

### Timing & Configuration

- Sensor read interval: e.g. 500 ms between reads; 3 reads per quantity → ~1.5 s per cycle.
- Cleaning: rinse duration (e.g. 10 s), dryer duration (e.g. 30 s), stabilisation window (e.g. 5 consecutive readings within baseline).
- All timings and thresholds in `config.h` or runtime config.

### Outputs of Phase 1

- Folder: `firmware/` (ESP32 project: `main/`, `include/`, platformio or Arduino structure).
- Docs: state diagram, pin mapping, calibration procedure.
- No dependency on cloud; all logic runs on ESP32 + optional local server.

---

## Phase 2 — Sensor Fusion & Data Pipeline

**Objective:** Build the signal-processing layer that turns raw sensor streams into a clean, multivariate feature vector for ML. Runs on Raspberry Pi or local PC (factory offline).

### Sub-Phases

| Sub-Phase | Title | Work |
|-----------|--------|------|
| **2.1** | Input interface and config | Define input source (Serial/TCP/HTTP from ESP32); config file for window sizes, baseline values, filter params. |
| **2.2** | Noise filtering per channel | Implement low-pass or median filter for pH, TDS, temperature, turbidity; configurable per channel. |
| **2.3** | Moving average smoothing | Rolling window (e.g. 5–10 samples) for each sensor; output smoothed stream. |
| **2.4** | Baseline normalization | Load baseline (e.g. distilled water) per sensor; subtract from smoothed values; store baseline in config. |
| **2.5** | Feature vector assembly | Build single array per sample: `[pH, TDS, temperature, turbidity]`; optional derived features. |
| **2.6** | Structured output and API | Output JSON/dict with timestamp (ISO8601); function `get_feature_vector()` for Phase 3; log raw and fused for debug. |
| **2.7** | Pipeline integration and tests | Wire Raw → Filter → Moving avg → Baseline → Feature vector; unit tests; validate with sample data. |

### Deliverables (Phase 2)

| Item | Description |
|------|-------------|
| Multivariate feature vector | Single array per sample: `[pH, TDS, temperature, turbidity]` (and optionally derived features) |
| Noise filtering | Optional low-pass or median filter per channel before fusion |
| Moving average smoothing | Configurable window (e.g. 5–10 samples) for each sensor in the stream |
| Baseline normalization | Subtract baseline (e.g. distilled water reading) per sensor; store baseline in config |
| Structured output | JSON/dict: `{ "pH": float, "tds": float, "temp": float, "turbidity": float, "timestamp": ISO8601 }` for ML and API |

### Implementation Notes

- Input: stream from ESP32 (Serial or TCP/HTTP).
- Pipeline: Raw → Filter → Moving average → Baseline correction → Feature vector.
- Output: one structured feature set per “sample” (e.g. per 3-read average from ESP32).
- Log raw and fused values for debugging and calibration validation.

### Outputs of Phase 2

- Folder: `sensor_fusion/` (e.g. Python package: `pipeline.py`, `filters.py`, `config.yaml`).
- Clear interface for Phase 3: `get_feature_vector()` or similar returning the array and metadata.

---

## Phase 3 — Machine Learning: Random Forest Regression (pH + Temperature → Citric & Ascorbic Acid %)

**Objective:** Multi-output regression from **pH** and **temperature** to **citric acid %** and **ascorbic acid %** using scikit-learn Random Forest Regressor. Model is trained on synthetic datasets (`citric_pH_temp_synthetic_600.csv`, `ascorbic_pH_temp_synthetic_600.csv`), merged by nearest (pH, temperature). Saved with joblib and exposed for production inference and Django API integration.

### Sub-Phases

| Sub-Phase | Title | Work |
|-----------|--------|------|
| **3.1** | Merge synthetic datasets | `ML_1/merge_datasets.py`: merge citric and ascorbic CSVs by nearest (pH, temperature) → `ML_1/dataset/combined_pH_temp_600.csv`. |
| **3.2** | Data loading module | `ML_1/load_dataset.py`: load combined CSV; features X = [pH, temperature_C]; targets y = [citric_percent_wv, ascorbic_percent_wv]. |
| **3.3** | Model training script | `ML_1/train_model.py`: 80/20 train/test split; train `RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)`; evaluate R², RMSE, MAE; save as `ML_1/models/random_forest_ph_temp.pkl`. |
| **3.4** | Prediction module | `ML_1/predict.py`: load model once; accept (pH, temperature); return `{citric_percent_wv, ascorbic_percent_wv}`. |
| **3.5** | Django API integration | `ML_1/model_service.py`: `predict_composition(sensor_data)`; input `{pH, temperature}`; return `{citric_acid, ascorbic_acid}`; load model once at startup. |
| **3.6** | Dataset and model layout | `ML_1/dataset/combined_pH_temp_600.csv`; `ML_1/models/random_forest_ph_temp.pkl`; README, requirements, installation instructions. |

### Dataset & Schema

| Item | Description |
|------|-------------|
| Source datasets | `citric_pH_temp_synthetic_600.csv`, `ascorbic_pH_temp_synthetic_600.csv` (project root) |
| Merged dataset | `ML_1/dataset/combined_pH_temp_600.csv` (600 rows) |
| CSV columns | `pH`, `temperature_C`, `citric_percent_wv`, `ascorbic_percent_wv` |
| Features (X) | pH, temperature_C |
| Targets (y) | citric_percent_wv, ascorbic_percent_wv |

### Model

| Item | Description |
|------|-------------|
| Algorithm | Random Forest Regressor (scikit-learn) |
| Parameters | `n_estimators=200`, `max_depth=10`, `random_state=42` |
| Multi-output | Single model for citric % and ascorbic % |
| Persistence | joblib; file `ML_1/models/random_forest_ph_temp.pkl` |

### API Contract (model_service.py)

- **Input:** `{ "pH": value, "temperature": value }`
- **Return:** `{ "citric_acid": predicted_value, "ascorbic_acid": predicted_value }`
- **Backend JSON output:** `{ "pH": 5.21, "citric_percent": 0.41, "ascorbic_percent": 0.17 }`

| Item | Description |
|------|-------------|
| Load model | Load from disk at startup; validate schema |
| Input | pH and temperature from sensors |
| Output | `predicted_citric_acid_pct`, `predicted_ascorbic_acid_pct` |
| Natural range check | Define acceptable ranges for natural coconut water; compare predictions |
| Authenticity decision | If any predicted value outside range → **Adulterated**; else **Authentic** |
| Logging | Log every inference: timestamp, input features, predictions, decision |

### Outputs of Phase 3

- **Folder structure:** `ML_1/merge_datasets.py`, `ML_1/load_dataset.py`, `ML_1/train_model.py`, `ML_1/predict.py`, `ML_1/model_service.py`, `ML_1/dataset/`, `ML_1/models/`.
- **Libraries:** pandas, numpy, scikit-learn, joblib.
- **Deliverables:** Merge script, training script, prediction function, model service, README, requirements.

---

## Phase 4 — Local Monitoring Interface & Cleaning/Reset Automation

**Objective:** Real-time local UI (Streamlit) and explicit cleaning/reset state transition logic (can be shared with firmware or implemented on Pi).

### Sub-Phases

| Sub-Phase | Title | Work |
|-----------|--------|------|
| **4.1** | Dashboard project and data source | Create Streamlit app structure; define how to fetch data (poll ESP32 or local ML server); config for refresh interval and URL. |
| **4.2** | Real-time live graphs | Implement live charts for pH, predicted Sugar %, Citric %, Ascorbic % (last N points or last 5 min); use Plotly or similar. |
| **4.3** | Final averaged reading display | Show latest 3-read (or fusion) averaged values clearly on dashboard. |
| **4.4** | Red alert box and alarm indicator | Prominent panel when status = Adulterated or threshold exceeded; visual alarm; optional sound. |
| **4.5** | Historical mini log | Scrollable table or list of last 20–50 readings with timestamp and authenticity decision. |
| **4.6** | System state display and auto-refresh | Display current state (Detecting / Cleaning / Ready, etc.); auto-refresh every 2–5 s from data source. |
| **4.7** | Cleaning automation — detection complete and trigger | Logic: when reading done and ML result received, trigger transition to cleaning; command/trigger for robotic arm to move to station. |
| **4.8** | Cleaning automation — rinse and dryer | Activate rinse for configured duration; then dryer for configured duration; state transitions RINSING → DRYING. |
| **4.9** | Cleaning automation — stabilisation and reset | Wait for pH in baseline range for M consecutive samples; reset flags (reading_done, alert); set state to READY; allow next DETECTING cycle. |
| **4.10** | State machine alignment and documentation | Align Python/automation state names with firmware; document transitions; optional shared automation module. |

### Streamlit Dashboard (Option A)

| Feature | Description |
|--------|-------------|
| Real-time live graphs | pH, predicted Sugar %, Citric %, Ascorbic % over time (e.g. last N points or last 5 min) |
| Final averaged reading display | Show latest 3-read (or fusion) averaged values clearly |
| Red alert box | Prominent panel when status = Adulterated or threshold exceeded |
| Alarm indicator | Visual + optional sound when alarm is active |
| Historical mini log | Scrollable table or list of last 20–50 readings with timestamp and decision |
| System state display | One of: Detecting | Cleaning | Ready (and optionally Idle, Stabilise) |
| Auto-refresh | Poll ESP32 or local ML server (e.g. every 2–5 s) to update graphs and state |

### Cleaning & Reset Automation (Logic)

| Step | Description |
|------|-------------|
| Detection complete | ESP32 or Pi marks “reading done”; result (authentic/adulterated) from ML |
| Move to cleaning station | Command/trigger to robotic arm (or simulated in logic) |
| Distilled water rinse | Activate rinse relay for configured duration |
| Dryer ON | Activate dryer for configured duration |
| Wait for pH baseline | Read pH until within baseline range (e.g. 6.8–7.2) for M consecutive samples over N seconds |
| Reset flags | Clear “reading_done”, “alert”; set state to READY |
| Allow next detection | State machine permits new DETECTING cycle |

Implement as state transition logic (Python or C) and document transitions; align with Phase 1 state names.

### Outputs of Phase 4

- Folder: `local_dashboard/` (Streamlit app: `app.py`, `components/`, `config.py`).
- Folder or section: `automation/` or inside `firmware/` for cleaning state machine (if not fully on ESP32).
- Requirements: `streamlit`, `pandas`, `plotly` or `matplotlib`, etc. in `requirements.txt`.

---

## Phase 5 — IoT Cloud Communication, Django Backend & Database

**Objective:** Reliable ESP32 → cloud data path, REST API, PostgreSQL schema, auth, and admin. Factory detection remains offline; cloud is for aggregation and transparency.

### Sub-Phases

| Sub-Phase | Title | Work |
|-----------|--------|------|
| **5.1** | IoT payload and endpoint design | Define JSON structure (timestamp, pH, tds, temperature, turbidity, predicted_*, status); design POST /api/upload-data/. |
| **5.2** | Upload error handling and retry | Retry with backoff (e.g. 3 attempts) on device/gateway; log failures; optional queue when offline. |
| **5.3** | Django project and app structure | Create project (config/, api/, core/); apps: readings, alerts, logs; base and production settings. |
| **5.4** | PostgreSQL models and migrations | Implement SensorReadings, Predictions, Alerts, SystemLogs, CalibrationData; indexes on timestamp and status; run migrations. |
| **5.5** | Serializers and upload API | Serializers for upload payload; validation; view and URL for POST /api/upload-data/; save to DB. |
| **5.6** | Aggregation endpoints (daily, weekly, monthly) | Implement /api/daily/, /api/weekly/, /api/monthly/ with query params; return aggregated data for frontend. |
| **5.7** | Authentication | Token or JWT for upload and admin; public read-only endpoints unauthenticated or key-based. |
| **5.8** | Admin panel and logging abnormal cases | Register models in Django admin; filters; on upload if status = adulterated or out-of-range, create Alert and SystemLog entry. |
| **5.9** | Schema documentation and env template | docs/database.md with schema diagram; .env.example for DATABASE_URL, SECRET_KEY, etc. |

### IoT Data Transmission

| Item | Description |
|------|-------------|
| Direction | ESP32 (or Raspberry Pi as gateway) → HTTP POST → Django API |
| JSON structure | `{ "timestamp", "pH", "tds", "temperature", "turbidity", "predicted_sugar", "predicted_citric", "predicted_ascorbic", "status" }` (status: e.g. "authentic" / "adulterated") |
| Endpoint | e.g. `POST /api/upload-data/` |
| Error handling | Retry with backoff (e.g. 3 attempts); log failures locally |
| Internet failure fallback | Queue payloads on device or Pi; send when connectivity restored; optional size limit |

### Django Backend

| Item | Description |
|------|-------------|
| Project structure | Standard Django project: `config/`, `api/`, `core/`, `apps/readings`, `apps/alerts`, etc. |
| REST API | Endpoints: `/api/upload-data/`, `/api/daily/`, `/api/weekly/`, `/api/monthly/` (query params: date, week, month) |
| PostgreSQL models | See Section 5.3 |
| Serializers | For SensorReadings, Predictions, Alerts; validation on upload |
| Authentication | Token or JWT for upload and for admin; public endpoints for dashboard read-only can be unauthenticated or key-based |
| Admin panel | Register models; filters for date, status; view alerts and system logs |
| Logging abnormal cases | On upload: if status = adulterated or out-of-range, create Alert and log to SystemLogs |

### Database Schema (PostgreSQL)

| Table | Purpose |
|-------|---------|
| **SensorReadings** | Raw/fused sensor data: id, timestamp, pH, tds, temperature, turbidity, source_device_id (optional) |
| **Predictions** | ML outputs: id, reading_id (FK), timestamp, predicted_sugar, predicted_citric, predicted_ascorbic, authenticity_status, confidence |
| **Alerts** | Abnormal events: id, timestamp, type (e.g. adulteration, sensor_fault), message, reading_id (nullable), resolved (boolean) |
| **SystemLogs** | Operational log: id, timestamp, level, component, message, metadata (JSON) |
| **CalibrationData** | Optional: store calibration run metadata or baseline values for traceability |

Define indexes on timestamp and status for fast daily/weekly/monthly queries.

### Outputs of Phase 5

- Folder: `backend/` (Django project + apps).
- `backend/requirements.txt`, `backend/config/settings/` (base, production).
- Migration files and schema diagram in `docs/database.md`.

---

## Phase 6 — React Frontend (Ceylon Coco), Deployment Architecture & Research Documentation

**Objective:** Public transparency dashboard, private admin dashboard, production deployment design, and academic-style documentation.

### Sub-Phases

| Sub-Phase | Title | Work |
|-----------|--------|------|
| **6.1** | Frontend project and API client | Create React app; set up routing (public vs admin); axios/fetch for Django APIs; Recharts or Chart.js. |
| **6.2** | Public dashboard — period selection and data fetch | Date / Week / Month selectors; fetch from /api/daily/, /api/weekly/, /api/monthly/; handle loading and errors. |
| **6.3** | Public dashboard — graphs and authenticity badge | Final averaged charts (pH, sugar %, citric %, ascorbic %); authenticity status badge (Authentic/Adulterated) with colour coding. |
| **6.4** | Public dashboard — ingredient transparency summary | Summary text and link to methodology; responsive layout. |
| **6.5** | Admin dashboard — raw data and predictions | Protected route; table or export of SensorReadings and Predictions with date/status filters. |
| **6.6** | Admin dashboard — alerts and system logs | Alerts list with resolve action; SystemLogs viewer with search/filter. |
| **6.7** | Deployment architecture design | Document factory (ESP32 + Pi, local ML, Streamlit) vs cloud (Django, PostgreSQL, React); env vars; production settings. |
| **6.8** | Security and environment template | HTTPS, CORS, secure cookies; rate limiting; .env.example; no secrets in repo. |
| **6.9** | Full data flow diagram | Final text/ASCII diagram: Sensors → ESP32 → Fusion → ML → Local UI → Cloud API → DB → Website; save in docs. |
| **6.10** | Research documentation (IEEE style) | Methodology (E-Tongue setup, sensors, calibration); calibration modelling table; mathematical formulation; innovation and industrial impact. |

### React Frontend — Public Customer Dashboard (Ceylon Coco Website)

| Feature | Description |
|--------|-------------|
| Date / Week / Month selection | Dropdowns or date pickers to choose reporting period |
| Final averaged graph | Charts (Recharts or Chart.js) for selected period: e.g. pH, sugar %, citric %, ascorbic % (aggregated as per API) |
| Authenticity status badge | Per batch or per day: Authentic / Adulterated with clear colour coding |
| Ingredient transparency summary | Short summary: “Predictions from our E-Tongue (sugar, citric, ascorbic) within natural ranges” and link to methodology |

Data source: Django `/api/daily/`, `/api/weekly/`, `/api/monthly/`.

### React Frontend — Private Admin Dashboard

| Feature | Description |
|--------|-------------|
| Full raw data | Table or export of SensorReadings and Predictions with filters |
| Alerts | List of Alerts with resolve action and filters |
| System logs | Searchable/filterable SystemLogs viewer |

Use same stack (Recharts/Chart.js), responsive layout, protected routes (auth).

### Deployment Architecture

| Layer | Placement |
|-------|------------|
| Factory (offline) | ESP32 + Raspberry Pi; local ML (Phase 3 inference); local Streamlit (Phase 4); no cloud required for detection |
| Cloud | Django on AWS / Railway / Render; PostgreSQL (managed); React on Vercel (or same provider) |
| Environment variables | All secrets and config via env (e.g. `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`, API keys); no secrets in repo |
| Production settings | Django: `DEBUG=False`, HTTPS, CORS whitelist, secure cookies; rate limiting on upload endpoint |
| Security | HTTPS only; auth for upload and admin; input validation and sanitisation; optional API key for device upload |

### Full Data Flow (Text Diagram)

```
[Sensors: pH, TDS, Temp, Turbidity]
        ↓
[ESP32: read → 3x avg → threshold check → buzzer if alert]
        ↓
[Serial / WiFi]
        ↓
[Raspberry Pi / Local PC]
        ↓
[Sensor Fusion: filter → moving avg → baseline norm] → [Feature vector]
        ↓
[ML Inference: load model → predict sugar, citric, ascorbic → range check → Authentic/Adulterated]
        ↓
[Local Streamlit Dashboard: real-time graphs, alert box, state, mini log]
        ↓
[Cleaning automation: arm → rinse → dry → stabilise → READY]
        ↓
[HTTP POST] (when online)
        ↓
[Django API: /api/upload-data/] → [PostgreSQL: SensorReadings, Predictions, Alerts, SystemLogs]
        ↓
[React: Public dashboard (daily/weekly/monthly, graphs, badge, transparency)]
[React: Admin dashboard (raw data, alerts, logs)]
```

### Research Documentation Support (IEEE Style)

Generate or outline in `docs/research/`:

- **Methodology:** E-Tongue setup, sensor choice, robotic integration, calibration protocol.
- **Calibration modelling:** How controlled samples (20–50) map measured (pH, TDS, T, turbidity) to sugar/citric/ascorbic; table of reference points (e.g. 0% sugar → pH 5.40, …).
- **Mathematical formulation:** Regression equations, feature vector, authenticity condition (ranges \(L_k, U_k\)).
- **Innovation justification:** Sensor fusion + regression for indirect quantification; no direct sugar/citric/ascorbic sensors; industrial applicability.
- **Industrial impact:** Traceability, consumer transparency, reduction of adulteration risk; scalability and offline-first design.

### Outputs of Phase 6

- Folder: `frontend/` (React app: public + admin routes, Recharts/Chart.js, responsive UI).
- Folder: `docs/` (deployment diagram, env template, `research/` with methodology and equations).
- Files: `docs/DEPLOYMENT.md`, `docs/research/METHODOLOGY.md`, `docs/DATA_FLOW.md`.

---

## Development Order Summary

1. **Phase 1** — Hardware and state machine (firmware).
2. **Phase 2** — Sensor fusion and feature pipeline (Python).
3. **Phase 3** — ML: dataset, training, evaluation, production inference, logging (full ML phase).
4. **Phase 4** — Local dashboard (Streamlit) and cleaning/reset automation logic.
5. **Phase 5** — Django API, PostgreSQL, IoT upload, auth, admin.
6. **Phase 6** — React frontends, deployment design, research documentation.

---

## Suggested Folder Structure (Final)

```
coconut-water-authenticity-detection-using-e-tongue/
├── phase.md                    # This file — do not update
├── README.md
├── docs/
│   ├── DATA_FLOW.md
│   ├── DEPLOYMENT.md
│   └── research/
│       └── METHODOLOGY.md
├── firmware/                   # Phase 1
│   ├── src/
│   ├── include/
│   └── platformio.ini (or Arduino)
├── sensor_fusion/              # Phase 2
│   ├── pipeline.py
│   ├── filters.py
│   └── config.yaml
├── ML_1/                       # Phase 3 (pH + temp → citric %, ascorbic %)
│   ├── dataset/
│   ├── models/
│   ├── merge_datasets.py
│   ├── load_dataset.py
│   ├── train_model.py
│   ├── predict.py
│   └── model_service.py
├── local_dashboard/            # Phase 4
│   ├── app.py
│   └── requirements.txt
├── backend/                    # Phase 5
│   ├── config/
│   ├── api/
│   └── requirements.txt
├── frontend/                   # Phase 6
│   ├── src/
│   └── package.json
└── automation/                 # Phase 4 (optional separate)
    └── cleaning_states.py
```

---

## Required Libraries (Consolidated)

- **Firmware:** ESP32 Arduino/PlatformIO, WiFi, HTTPClient, driver libs for pH/TDS/temp/turbidity.
- **Sensor fusion & ML:** Python 3.9+, `numpy`, `pandas`, `scikit-learn`, `pyyaml`, `joblib` (or `pickle`).
- **Local dashboard:** `streamlit`, `pandas`, `plotly` or `matplotlib`, `requests`.
- **Backend:** `Django`, `djangorestframework`, `django-cors-headers`, `psycopg2-binary`, `gunicorn`, `python-dotenv`.
- **Frontend:** `react`, `react-router-dom`, `recharts` or `chart.js`, `axios`, `date-fns` (or similar).

---

*End of phase plan. Use this document as the single source of truth for phase order and scope; do not modify this file.*
