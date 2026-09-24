# ML_2 — Phase 3: Four sensors → Sugar %

Random Forest model: **input** pH, TDS, temperature, turbidity → **output** sugar % (Brix).

Training data combines:
- **Literature** Brix–TDS curve (coconut water, 400 synthetic rows)
- **Calibration** dataset (`ml/data/calibration/calibration_dataset.csv`, 82 rows)

## Folder structure

```
ML_2/
├── dataset/
│   ├── literature_tds_sugar_synthetic.csv   # from generate_sugar_tds_literature_dataset.py
│   ├── literature_tds_brix_anchor.csv
│   └── combined_sensors_sugar.csv           # merged training file
├── models/
│   └── random_forest_sugar_sensors.pkl
├── merge_datasets.py
├── load_dataset.py
├── train_model.py
├── predict.py
├── model_service.py
├── run_predict.py
└── requirements.txt
```

## Setup and train

From **project root**:

```powershell
pip install -r ML_2/requirements.txt
python generate_sugar_tds_literature_dataset.py
python ML_2/merge_datasets.py
python ML_2/train_model.py
```

## Predict

```powershell
python ML_2/run_predict.py 5.5 3500 25 20
```

```python
from ML_2.predict import predict
out = predict(pH=5.5, tds=3500, temperature=25, turbidity=20)
# out["sugar_pct"]
```

## Django API

```python
from ML_2.model_service import predict_sugar
result = predict_sugar({"pH": 5.5, "tds": 3500, "temperature": 25, "turbidity": 20})
# result["sugar"]
```

## With ML_1 (full composition)

| Module | Inputs | Outputs |
|--------|--------|---------|
| **ML_1** | pH, temperature | citric %, ascorbic % |
| **ML_2** | pH, TDS, temperature, turbidity | sugar % |
