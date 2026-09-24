"""Add MSE to regression metrics CSVs and print a report table."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DESKTOP = Path.home() / "Desktop" / "chapter4_graphs"
FILES = [
    ROOT / "docs" / "research" / "figures" / "chapter4_regression_metrics.csv",
    ROOT / "docs" / "research" / "figures" / "ml1_acid_regression_metrics.csv",
]


def with_mse(path: Path) -> list[dict]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out = []
    for r in rows:
        mae = float(r["MAE"])
        rmse = float(r["RMSE"])
        r2 = float(r["R2"])
        mse = rmse**2
        out.append(
            {
                "Target": r["Target"],
                "MAE": mae,
                "MSE": mse,
                "RMSE": rmse,
                "R2": r2,
            }
        )
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Target", "MAE", "MSE", "RMSE", "R2"])
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    DESKTOP.mkdir(parents=True, exist_ok=True)
    chapter = with_mse(FILES[0])
    ml1 = with_mse(FILES[1])

    write_csv(FILES[0], chapter)
    write_csv(DESKTOP / "chapter4_regression_metrics.csv", chapter)
    write_csv(FILES[1], ml1)
    write_csv(DESKTOP / "ml1_acid_regression_metrics.csv", ml1)

    md = ROOT / "docs" / "research" / "mae_mse_r2_summary.md"
    lines = [
        "# MAE / MSE / RMSE / R² by Target",
        "",
        "Sugar from **ML_2** (4 sensors). Citric & ascorbic from **ML_1** (pH + temperature).",
        "",
        "| Target | MAE | MSE | RMSE | R² |",
        "|--------|----:|----:|-----:|---:|",
    ]
    print("Target | MAE | MSE | RMSE | R2")
    print("-" * 72)
    for r in chapter:
        lines.append(
            f"| {r['Target']} | {r['MAE']:.6g} | {r['MSE']:.6g} | {r['RMSE']:.6g} | {r['R2']:.4f} |"
        )
        print(
            f"{r['Target']}: MAE={r['MAE']:.6g}, MSE={r['MSE']:.6g}, "
            f"RMSE={r['RMSE']:.6g}, R2={r['R2']:.4f}"
        )
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {md}")
    print(f"Wrote CSVs under figures/ and {DESKTOP}")


if __name__ == "__main__":
    main()
