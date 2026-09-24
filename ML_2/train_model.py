"""
Train Random Forest: pH, TDS, temperature, turbidity -> sugar_pct.

Run from project root:
  python ML_2/merge_datasets.py
  python ML_2/train_model.py
"""
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

try:
    from load_dataset import TARGET_COLUMN, load_xy
except ImportError:
    from ML_2.load_dataset import TARGET_COLUMN, load_xy

RANDOM_STATE = 42
TEST_SIZE = 0.2
MODEL_PARAMS = {"n_estimators": 200, "max_depth": 12, "random_state": RANDOM_STATE}


def get_models_dir() -> Path:
    return Path(__file__).resolve().parent / "models"


def train_and_evaluate(csv_path: str | Path | None = None) -> RandomForestRegressor:
    X, y = load_xy(csv_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    model = RandomForestRegressor(**MODEL_PARAMS)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)

    print("Evaluation (test set) — sugar prediction:")
    print("-" * 50)
    print(f"  {TARGET_COLUMN}: R2={r2:.4f}, RMSE={rmse:.4f}, MAE={mae:.4f}")
    print("-" * 50)
    return model


def save_model(model: RandomForestRegressor, path: str | Path | None = None) -> Path:
    out_dir = get_models_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = path or out_dir / "random_forest_sugar_sensors.pkl"
    joblib.dump(model, out_path)
    print(f"Model saved to {out_path}")
    return Path(out_path)


if __name__ == "__main__":
    model = train_and_evaluate()
    save_model(model)
