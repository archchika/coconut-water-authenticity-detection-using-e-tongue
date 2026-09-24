"""
Generate UPDATED coconut-water acid calibration curves from ML_1 literature data.

Source: ML_1/dataset/combined_pH_temp_600.csv
        (digitized maturation curves: pH vs citric % and ascorbic %)

Outputs PNG + JPG to:
  - calibration_curves/
  - docs/research/figures/
  - Desktop/chapter4_graphs/
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "ML_1" / "dataset" / "combined_pH_temp_600.csv"
ANCHORS = ROOT / "ML_1" / "dataset" / "literature_maturation_anchors.csv"
OUT_DIRS = [
    ROOT / "calibration_curves",
    ROOT / "docs" / "research" / "figures",
    Path.home() / "Desktop" / "chapter4_graphs",
]


def save_all(fig: plt.Figure, stem: str) -> None:
    for d in OUT_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        png = d / f"{stem}.png"
        jpg = d / f"{stem}.jpg"
        fig.savefig(png, dpi=300, bbox_inches="tight")
        fig.savefig(jpg, dpi=300, bbox_inches="tight", format="jpeg", pil_kwargs={"quality": 95})
        # ensure true JPEG via Pillow (matplotlib jpeg can vary)
        Image.open(png).convert("RGB").save(jpg, "JPEG", quality=95, optimize=True)
        print(f"saved: {jpg}")


def main() -> None:
    df = pd.read_csv(DATA).dropna()
    anchors = pd.read_csv(ANCHORS) if ANCHORS.exists() else None

    # ── Main side-by-side calibration (replaces old INS additive graph) ──────
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax1 = axes[0]
    s1 = ax1.scatter(
        df["pH"],
        df["citric_percent_wv"],
        c=df["temperature_C"],
        cmap="viridis",
        alpha=0.65,
        s=28,
        edgecolors="none",
    )
    if anchors is not None:
        ax1.plot(
            anchors["pH_citric_curve"],
            anchors["citric_percent_wv"],
            "r--o",
            linewidth=1.5,
            markersize=6,
            label="Literature anchors",
        )
        ax1.legend(fontsize=8, loc="upper right")
    ax1.set_xlabel("pH")
    ax1.set_ylabel("Citric acid (% w/v)")
    ax1.set_title("Citric acid — coconut water maturation\n(pH vs concentration)")
    ax1.grid(True, alpha=0.3)
    plt.colorbar(s1, ax=ax1, label="Temperature (°C)")

    ax2 = axes[1]
    s2 = ax2.scatter(
        df["pH"],
        df["ascorbic_percent_wv"],
        c=df["temperature_C"],
        cmap="plasma",
        alpha=0.65,
        s=28,
        edgecolors="none",
    )
    if anchors is not None:
        ax2.plot(
            anchors["pH_ascorbic_curve"],
            anchors["ascorbic_percent_wv"],
            "r--s",
            linewidth=1.5,
            markersize=6,
            label="Literature anchors",
        )
        ax2.legend(fontsize=8, loc="upper right")
    ax2.set_xlabel("pH")
    ax2.set_ylabel("Ascorbic acid (% w/v)")
    ax2.set_title("Ascorbic acid — coconut water maturation\n(pH vs concentration)")
    ax2.grid(True, alpha=0.3)
    plt.colorbar(s2, ax=ax2, label="Temperature (°C)")

    fig.suptitle(
        "Updated calibration curves (ML_1 literature dataset)",
        fontsize=13,
        y=1.02,
    )
    fig.tight_layout()
    save_all(fig, "calibration_curves_ph_vs_acid")
    plt.close(fig)

    # ── Stacked view ─────────────────────────────────────────────────────────
    fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(8, 9))
    ax3.scatter(df["pH"], df["citric_percent_wv"], alpha=0.55, s=22, color="#059669", label="Citric")
    if anchors is not None:
        ax3.plot(
            anchors["pH_citric_curve"],
            anchors["citric_percent_wv"],
            "k--o",
            linewidth=1.4,
            label="Literature anchors",
        )
    ax3.set_xlabel("pH")
    ax3.set_ylabel("Citric acid (% w/v)")
    ax3.set_title("Citric acid: pH vs concentration (coconut water)")
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=8)

    ax4.scatter(df["pH"], df["ascorbic_percent_wv"], alpha=0.55, s=22, color="#7c3aed", label="Ascorbic")
    if anchors is not None:
        ax4.plot(
            anchors["pH_ascorbic_curve"],
            anchors["ascorbic_percent_wv"],
            "k--s",
            linewidth=1.4,
            label="Literature anchors",
        )
    ax4.set_xlabel("pH")
    ax4.set_ylabel("Ascorbic acid (% w/v)")
    ax4.set_title("Ascorbic acid: pH vs concentration (coconut water)")
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=8)

    fig2.tight_layout()
    save_all(fig2, "calibration_curves_combined")
    plt.close(fig2)

    # ── By temperature bins ──────────────────────────────────────────────────
    fig3, axes3 = plt.subplots(2, 2, figsize=(12, 9))
    bins = [
        (axes3[0, 0], "Citric acid (18–24°C)", df[df["temperature_C"].between(18, 24)], "citric_percent_wv"),
        (axes3[0, 1], "Citric acid (25–32°C)", df[df["temperature_C"].between(25, 32)], "citric_percent_wv"),
        (axes3[1, 0], "Ascorbic acid (18–24°C)", df[df["temperature_C"].between(18, 24)], "ascorbic_percent_wv"),
        (axes3[1, 1], "Ascorbic acid (25–32°C)", df[df["temperature_C"].between(25, 32)], "ascorbic_percent_wv"),
    ]
    for ax, title, sub, col in bins:
        ax.scatter(sub["pH"], sub[col], alpha=0.6, s=22)
        ax.set_xlabel("pH")
        ax.set_ylabel(col.replace("_", " "))
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
    fig3.suptitle("Calibration by temperature band (updated ML_1 data)", fontsize=12)
    fig3.tight_layout()
    save_all(fig3, "calibration_curves_by_temperature")
    plt.close(fig3)

    print("\nUpdated coconut-water calibration curves generated.")
    print(f"Data rows: {len(df)}")
    print(
        f"pH {df['pH'].min():.2f}-{df['pH'].max():.2f} | "
        f"citric {df['citric_percent_wv'].min():.4f}-{df['citric_percent_wv'].max():.4f}% | "
        f"ascorbic {df['ascorbic_percent_wv'].min():.6f}-{df['ascorbic_percent_wv'].max():.6f}%"
    )


if __name__ == "__main__":
    main()
