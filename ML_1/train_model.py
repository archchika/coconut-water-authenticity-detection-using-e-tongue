"""
Phase 3.2 — Train Random Forest: pH, temperature -> citric_percent_wv, ascorbic_percent_wv.
"""
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

try:
    from load_dataset import TARGET_COLUMNS, load_xy
except ImportError:
    from ML_1.load_dataset import TARGET_COLUMNS, load_xy

RANDOM_STATE = 42
TEST_SIZE = 0.2
MODEL_PARAMS = {"n_estimators": 200, "max_depth": 10, "random_state": RANDOM_STATE}


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

    print("Evaluation (test set):")
    print("-" * 50)
    for i, name in enumerate(TARGET_COLUMNS):
        r2 = r2_score(y_test[:, i], y_pred[:, i])
        rmse = np.sqrt(mean_squared_error(y_test[:, i], y_pred[:, i]))
        mae = mean_absolute_error(y_test[:, i], y_pred[:, i])
        print(f"  {name}: R2={r2:.4f}, RMSE={rmse:.4f}, MAE={mae:.4f}")
    r2_avg = r2_score(y_test, y_pred)
    rmse_avg = np.sqrt(mean_squared_error(y_test, y_pred))
    mae_avg = mean_absolute_error(y_test, y_pred)
    print("-" * 50)
    print(f"  (average): R2={r2_avg:.4f}, RMSE={rmse_avg:.4f}, MAE={mae_avg:.4f}")
    return model


def save_model(model: RandomForestRegressor, path: str | Path | None = None) -> Path:
    out_dir = get_models_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = path or out_dir / "random_forest_ph_temp.pkl"
    joblib.dump(model, out_path)
    print(f"Model saved to {out_path}")
    return Path(out_path)


if __name__ == "__main__":
    model = train_and_evaluate()
    save_model(model)
