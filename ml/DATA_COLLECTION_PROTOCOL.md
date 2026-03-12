# Phase 3.1 — Data collection protocol for calibration (20–50 controlled samples)

Protocol for building the calibration dataset used to train the E-Tongue regression models (sugar %, citric acid %, ascorbic acid %).

---

## Objective

Collect **20–50 controlled samples** (or more) where:

- **Inputs (measured by E-Tongue):** pH, TDS, temperature, turbidity.
- **Outputs (known reference):** sugar_pct, citric_acid_pct, ascorbic_acid_pct.

Samples must cover the range of interest for natural and borderline/adulterated coconut water so the model can learn the mapping.

---

## Equipment and preparation

1. **E-Tongue setup:** Same sensors and calibration as in production (ESP32 + pH, TDS, temperature, turbidity). Ensure probes are calibrated (see `firmware/CALIBRATION_PROCEDURE.md`).
2. **Reference concentrations:** Prepare solutions with **known** sugar %, citric acid %, ascorbic acid % (e.g. from lab analysis or prepared standards).
3. **Environment:** Stable temperature where possible; record ambient conditions in `notes` if needed.
4. **Rinse between samples:** Use distilled water and drying per cleaning protocol to avoid carry-over.

---

## Sample design (20–50 samples)

- **Spread over the natural range:** Include low, mid, and high values for each target within the range of interest (e.g. sugar 0–4%, citric 0.1–0.3%, ascorbic 0.01–0.05% — adjust from literature or your design).
- **Grid or factorial:** Optionally use a design (e.g. 5 levels × 4 repeats, or factorial combinations) to cover the space.
- **Replicates:** At least 2–3 replicates per distinct concentration set improve robustness.
- **Minimum:** 20 samples; **recommended:** 30–50 for stable regression and validation split.

---

## Procedure per sample

1. **Assign `sample_id`** (e.g. S001, S002, …) and note in the CSV.
2. **Prepare the sample** (solution or coconut water with known or measured reference values for sugar_pct, citric_acid_pct, ascorbic_acid_pct).
3. **Stabilise sensors:** After rinse/dry, wait for sensor stabilisation (e.g. pH baseline or stable readings).
4. **Record sensor outputs:** Take one or more averaged readings (e.g. 3× average as in firmware). Enter **pH, TDS, temperature, turbidity** in the CSV (use mean if multiple reads).
5. **Enter reference values:** Fill **sugar_pct, citric_acid_pct, ascorbic_acid_pct** from your reference (prepared concentration or lab result).
6. **Notes:** Add any relevant info (batch, date, preparation, outlier note).
7. **Rinse and dry** before the next sample.

---

## CSV and schema

- Use the **CSV schema** in `ml/training/SCHEMA.md`.
- Start from **`ml/data/calibration/calibration_template.csv`** or create a new file with the same header.
- Save as UTF-8, comma-separated; one row per sample (after header).
- Final file: e.g. **`ml/data/calibration/calibration_dataset.csv`** for use in Phase 3.2 (load and validation).

---

## Quality checks (before training)

- No missing values in required columns (or document and handle in 3.2).
- Ranges: pH, TDS, temperature, turbidity within expected sensor range; sugar/citric/ascorbic non-negative and within design range.
- Duplicate `sample_id`s: resolve or drop duplicates.
- Outliers: note in `notes`; decide whether to exclude before training (document in 3.2).

---

## References (to fill per project)

- Natural coconut water ranges (sugar, citric, ascorbic) from literature or in-house data.
- Standard solutions and lab method for reference concentrations (if used).
