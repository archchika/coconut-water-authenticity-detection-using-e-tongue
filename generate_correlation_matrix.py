"""
Generate Pearson correlation matrix heatmap for E-Tongue feature analysis.
Output used for report Data Analysis section.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

CSV_PATH = Path(__file__).parent / "ML_2" / "dataset" / "combined_sensors_sugar.csv"
OUT_DIR = Path(__file__).parent / "docs" / "research" / "figures"

COLUMNS = [
    "pH",
    "TDS",
    "temperature",
    "turbidity",
    "sugar_pct",
    "citric_acid_pct",
    "ascorbic_acid_pct",
]
LABELS = [
    "pH",
    "TDS",
    "Temperature",
    "Turbidity",
    "Sugar %",
    "Citric %",
    "Ascorbic %",
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(CSV_PATH)
    data = df[COLUMNS].dropna()
    corr = data.corr(method="pearson")

    fig, ax = plt.subplots(figsize=(9.5, 7.5))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)

    ax.set_xticks(range(len(LABELS)))
    ax.set_yticks(range(len(LABELS)))
    ax.set_xticklabels(LABELS, rotation=45, ha="right")
    ax.set_yticklabels(LABELS)

    for i in range(len(LABELS)):
        for j in range(len(LABELS)):
            val = corr.values[i, j]
            color = "white" if abs(val) >= 0.55 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=color, fontsize=10)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Pearson correlation", rotation=90)

    ax.set_title("Correlation Matrix: Sensor Features vs Composition Targets")
    fig.tight_layout()

    png_path = OUT_DIR / "correlation_matrix_features_vs_composition.png"
    pdf_path = OUT_DIR / "correlation_matrix_features_vs_composition.pdf"
    csv_out = OUT_DIR / "correlation_matrix_features_vs_composition.csv"

    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")

    desktop = Path.home() / "Desktop" / "chapter4_graphs"
    desktop.mkdir(parents=True, exist_ok=True)
    fig.savefig(desktop / png_path.name, dpi=300, bbox_inches="tight")
    plt.close(fig)

    corr_labeled = corr.copy()
    corr_labeled.index = LABELS
    corr_labeled.columns = LABELS
    corr_labeled.to_csv(csv_out)
    corr_labeled.to_csv(desktop / csv_out.name)

    print(f"rows: {len(data)}")
    print(f"saved: {png_path}")
    print(f"saved: {pdf_path}")
    print(f"saved: {csv_out}")
    print(f"copied to: {desktop}")
    print(corr_labeled.round(3).to_string())


if __name__ == "__main__":
    main()
