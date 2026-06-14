"""
Generate calibration curves from citric and ascorbic acid CSV data.
Output: calibration curves showing pH vs acid concentration (% w/v).
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

CITRIC_CSV = Path(__file__).parent / "citric_pH_temp_synthetic_600.csv"
ASCORBIC_CSV = Path(__file__).parent / "ascorbic_pH_temp_synthetic_600.csv"
OUTPUT_DIR = Path(__file__).parent / "calibration_curves"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load data
    citric = pd.read_csv(CITRIC_CSV)
    ascorbic = pd.read_csv(ASCORBIC_CSV)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # --- Citric acid: pH vs citric_percent_wv ---
    ax1 = axes[0]
    scatter1 = ax1.scatter(
        citric["pH"],
        citric["citric_percent_wv"],
        c=citric["temperature_C"],
        cmap="viridis",
        alpha=0.6,
        s=25,
    )
    ax1.set_xlabel("pH")
    ax1.set_ylabel("Citric acid (% w/v)")
    ax1.set_title("Citric acid calibration curve (pH vs concentration)")
    ax1.grid(True, alpha=0.3)
    cbar1 = plt.colorbar(scatter1, ax=ax1, label="Temperature (°C)")

    # --- Ascorbic acid: pH vs ascorbic_percent_wv ---
    ax2 = axes[1]
    scatter2 = ax2.scatter(
        ascorbic["pH"],
        ascorbic["ascorbic_percent_wv"],
        c=ascorbic["temperature_C"],
        cmap="plasma",
        alpha=0.6,
        s=25,
    )
    ax2.set_xlabel("pH")
    ax2.set_ylabel("Ascorbic acid (% w/v)")
    ax2.set_title("Ascorbic acid calibration curve (pH vs concentration)")
    ax2.grid(True, alpha=0.3)
    cbar2 = plt.colorbar(scatter2, ax=ax2, label="Temperature (°C)")

    plt.tight_layout()
    out_path = OUTPUT_DIR / "calibration_curves_ph_vs_acid.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")

    # --- Combined: pH vs both acids (separate subplots) ---
    fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(8, 10))

    ax3.scatter(citric["pH"], citric["citric_percent_wv"], alpha=0.5, s=20, color="#059669", label="Citric")
    ax3.set_xlabel("pH")
    ax3.set_ylabel("Citric acid (% w/v)")
    ax3.set_title("Citric acid: pH vs concentration")
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    ax4.scatter(ascorbic["pH"], ascorbic["ascorbic_percent_wv"], alpha=0.5, s=20, color="#7c3aed", label="Ascorbic")
    ax4.set_xlabel("pH")
    ax4.set_ylabel("Ascorbic acid (% w/v)")
    ax4.set_title("Ascorbic acid: pH vs concentration")
    ax4.grid(True, alpha=0.3)
    ax4.legend()

    plt.tight_layout()
    out_path2 = OUTPUT_DIR / "calibration_curves_combined.png"
    plt.savefig(out_path2, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path2}")

    # --- Temperature effect: pH vs acid at fixed temp bins ---
    fig3, axes3 = plt.subplots(2, 2, figsize=(12, 10))

    for i, (ax, title, df, col) in enumerate([
        (axes3[0, 0], "Citric acid (20–24°C)", citric[citric["temperature_C"].between(20, 24)], "citric_percent_wv"),
        (axes3[0, 1], "Citric acid (25–30°C)", citric[citric["temperature_C"].between(25, 30)], "citric_percent_wv"),
        (axes3[1, 0], "Ascorbic acid (20–24°C)", ascorbic[ascorbic["temperature_C"].between(20, 24)], "ascorbic_percent_wv"),
        (axes3[1, 1], "Ascorbic acid (25–30°C)", ascorbic[ascorbic["temperature_C"].between(25, 30)], "ascorbic_percent_wv"),
    ]):
        ax.scatter(df["pH"], df[col], alpha=0.6, s=20)
        ax.set_xlabel("pH")
        ax.set_ylabel(col.replace("_", " ").replace("wv", "") + " (%)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path3 = OUTPUT_DIR / "calibration_curves_by_temperature.png"
    plt.savefig(out_path3, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path3}")

    print("\nCalibration curves generated successfully.")


if __name__ == "__main__":
    main()
