# ML_1 — Phase 3: pH + Temperature → Citric % & Ascorbic %

Random Forest model: **input** pH and temperature → **output** citric acid % and ascorbic acid % (w/v).

## Folder structure (Phase 3.6)

```
ML_1/
├── dataset/
│   └── combined_pH_temp_600.csv    # 600 rows: pH, temperature_C, citric_percent_wv, ascorbic_percent_wv
├── models/
│   └── random_forest_ph_temp.pkl   # Trained Random Forest (joblib)
├── merge_datasets.py               # Phase 3.1: merge citric + ascorbic CSVs
├── load_dataset.py                 # Phase 3.2: load features & targets
├── train_model.py                  # Phase 3.3: train (80/20 split), evaluate, save
├── predict.py                      # Phase 3.4: predict(pH, temperature)
├── model_service.py                # Phase 3.5: predict_composition() for Django API
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r ML_1/requirements.txt
```

**Requirements:** pandas, numpy, scikit-learn, joblib

## Usage

### 1. Merge datasets (Phase 3.1 — run once from project root)

```bash
python ML_1/merge_datasets.py
```

### 2. Train model (Phase 3.3 — 80% train, 20% test)

```bash
python ML_1/train_model.py
```

### 3. Predict (Phase 3.4)

```python
from ML_1.predict import predict
out = predict(pH=3.5, temperature=25.0)
# out["citric_percent_wv"], out["ascorbic_percent_wv"]
```

### 4. Django API (Phase 3.5)

```python
from ML_1.model_service import predict_composition
result = predict_composition({"pH": 3.5, "temperature": 25.0})
# result["citric_acid"], result["ascorbic_acid"]
```

## Data sources

- `citric_pH_temp_synthetic_600.csv` — INS 330 (citric acid)
- `ascorbic_pH_temp_synthetic_600.csv` — INS 300 (ascorbic acid)

Merged by nearest (pH, temp) → `dataset/combined_pH_temp_600.csv`.
