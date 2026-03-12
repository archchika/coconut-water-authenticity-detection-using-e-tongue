# IoT-Based E-Tongue System for Coconut Water Authenticity Detection

Industrial-grade research prototype: **Sensor Fusion, Regression Modeling, Robotic Integration, and Web Transparency Platform.**

**Repository:** [coconut-water-authenticity-detection-using-e-tongue](https://github.com/archchika/coconut-water-authenticity-detection-using-e-tongue)

---

## Overview

E-Tongue system for detecting coconut water authenticity before packaging using:

- **Sensors:** pH (primary), TDS (sugar estimation), Temperature (compensation), Turbidity (suspended solids)
- **Indirect estimation:** Regression from sensor readings → sugar %, citric acid %, ascorbic acid %
- **Decision:** Predictions outside natural range → **Adulterated**; else **Authentic**

System runs **offline in factory** for detection; cloud used for aggregation and consumer transparency.

---

## Project Structure

```
├── phase.md                 # 6-phase development plan (do not modify)
├── firmware/                # Phase 1: ESP32 firmware
├── sensor_fusion/           # Phase 2: Feature pipeline
├── ml/                      # Phase 3: Training & inference
├── local_dashboard/         # Phase 4: Streamlit UI + automation
├── backend/                 # Phase 5: Django API + PostgreSQL
├── frontend/                # Phase 6: React (Ceylon Coco)
├── docs/                    # Deployment & research docs
└── automation/              # Cleaning/reset state logic
```

---

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- ESP32 toolchain (Arduino IDE or PlatformIO)
- PostgreSQL (for backend)

### 1. Sensor Fusion + ML (local)

```bash
cd sensor_fusion && pip install -r requirements.txt
cd ../ml && pip install -r requirements.txt
# Add calibration data to ml/data/calibration/ then run training (see ml/README.md)
```

### 2. Local dashboard

```bash
cd local_dashboard && pip install -r requirements.txt && streamlit run app.py
```

### 3. Backend

```bash
cd backend && pip install -r requirements.txt
cp .env.example .env  # Edit with DB URL, SECRET_KEY
python manage.py migrate && python manage.py runserver
```

### 4. Frontend

```bash
cd frontend && npm install && npm run dev
```

### 5. Firmware (Phase 1 complete)

Open `firmware/` in PlatformIO or Arduino IDE; set WiFi and pin defines in `include/config.h`; upload to ESP32. See `firmware/README.md`, `firmware/STATE_DIAGRAM.md`, and `firmware/CALIBRATION_PROCEDURE.md`.

---

## Development Order

Follow **phase.md**: Phase 1 → 2 → 3 → 4 → 5 → 6.

### Phase 3 — ML (training and inference)

- **3.1** — Dataset schema and collection protocol: CSV schema and 20–50 sample protocol in **`ml/`**. See **`ml/training/SCHEMA.md`**, **`ml/DATA_COLLECTION_PROTOCOL.md`**, **`ml/data/calibration/calibration_dataset.csv`** (from **`coconut_water_ml_dataset.md`**), and **`ml/README.md`**.
- **3.2** — Data load and validation: **`ml/training/load_data.py`** loads CSV, validates (missing, ranges, duplicates), and **`train_val_split`** does 80/20 split with **seed=42**. Run **`python ml/training/run_load_validate.py`** to print report and shapes.
- **3.3** — Feature scaling: **`ml/training/scaling.py`** fits StandardScaler (or MinMaxScaler) on **train only**, saves scaler to **`ml/models/v1/scaler.joblib`** for production. Run **`python ml/training/run_scale_save.py`** to fit and save.

### Phase 5 — Backend API

- **5.1** — IoT payload and endpoint design: **POST /api/upload-data/** and JSON structure in **[docs/phase5-upload-api-spec.md](docs/phase5-upload-api-spec.md)**. Optional JSON Schema: `docs/upload-data-payload.schema.json`.
- **5.2** — Upload error handling and retry: **Firmware** uses exponential backoff and Serial logging (see `firmware/src/transport.cpp`). **Gateway:** **`backend/upload_client.py`** provides `upload_reading()` (retry + backoff + logging) and optional **`UploadQueue`** for offline queue. See **[docs/phase5-2-upload-error-handling.md](docs/phase5-2-upload-error-handling.md)**.

---

## License

Research / academic use. See repository for details.
