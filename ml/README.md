# ML Module — E-Tongue Random Forest Regression (Phase 3)

Multi-output regression from sensor features to composition using **only** scikit-learn `RandomForestRegressor`.

## Folder structure

```
ml/
  dataset/
    coconut_data.csv      # CSV: pH, TDS, Turbidity, Temperature, Sugar_percent, Citric_percent, Ascorbic_percent
  models/
    random_forest_etongue.pkl   # Trained model (created by train_model.py)
  load_dataset.py         # Load CSV; separate X, y; handle missing values
  train_model.py          # Train RF; evaluate R2/RMSE/MAE; save model
  predict.py              # Load model once; predict(Sugar, Citric, Ascorbic)
  model_service.py        # predict_composition(sensor_data) for Django backend
  run_example_prediction.py   # Example test script
  requirements.txt
  README.md
```

## Installation

From project root or `ml/`:

```bash
pip install -r ml/requirements.txt
```

Libraries: `pandas`, `numpy`, `scikit-learn`, `joblib`.

## 1. Data

- **CSV columns:** `pH`, `TDS`, `Turbidity`, `Temperature`, `Sugar_percent`, `Citric_percent`, `Ascorbic_percent`
- **Example row:** `5.32,315,3.4,27,2.0,0.40,0.15`
- Place your data at `ml/dataset/coconut_data.csv` (400+ samples recommended).

## 2. Train model

From **project root**:

```bash
cd ml && python train_model.py
```

Or:

```bash
python -m ml.train_model
```

This will:

- Load `ml/dataset/coconut_data.csv`
- Split 80/20 train/test
- Train `RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)`
- Print R2, RMSE, MAE per target
- Save the model to `ml/models/random_forest_etongue.pkl`

## 3. Prediction (standalone)

```python
from ml.predict import predict

out = predict(pH=5.21, TDS=340, Turbidity=3.2, Temperature=27)
# out["Sugar_percent"], out["Citric_percent"], out["Ascorbic_percent"]
```

## 4. Django backend integration

Use `model_service.predict_composition(sensor_data)`:

**Input:**

```python
sensor_data = {
    "pH": 5.21,
    "TDS": 340,
    "turbidity": 3.2,
    "temperature": 27,
}
```

**Return:**

```python
{
    "sugar": 2.8,
    "citric_acid": 0.41,
    "ascorbic_acid": 0.17,
}
```

For the final API response (with pH and rounded percentages):

```python
from ml.model_service import predict_composition_for_api
result = predict_composition_for_api(sensor_data)
# {"pH": 5.21, "sugar_percent": 2.8, "citric_percent": 0.41, "ascorbic_percent": 0.17}
```

The model is loaded **once** at first use (global singleton in `predict.py`); load it at Django startup if you want to avoid latency on the first request.

## 5. Example test script

```bash
cd ml && python run_example_prediction.py
```

Requires a trained model at `ml/models/random_forest_etongue.pkl` (run `train_model.py` first).

## Summary

| Task              | Command / Module                    |
|-------------------|-------------------------------------|
| Install deps      | `pip install -r ml/requirements.txt` |
| Train             | `cd ml && python train_model.py`    |
| Example prediction| `cd ml && python run_example_prediction.py` |
| Django integration| `from ml.model_service import predict_composition` |
