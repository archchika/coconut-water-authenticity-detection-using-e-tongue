# Methodology and Formulation for Coconut Water Authenticity Using an E-Tongue (Phase 6.10)

*IEEE-style research documentation outline. Replace placeholders with experimental data and references.*

---

## Abstract

An electronic tongue (E-Tongue) system for coconut water authenticity assessment is described. Multi-sensor measurements (pH, TDS, temperature, turbidity) are fused and used in a calibrated regression model to predict sugar, citric acid, and ascorbic acid levels. Predictions are compared to natural ranges to classify batches as *Authentic* or *Adulterated*. The methodology covers sensor choice, calibration protocol, mathematical formulation, and deployment (offline factory + cloud). The approach enables traceability and consumer transparency without direct sugar/citric/ascorbic sensors.

**Index Terms** — Coconut water, electronic tongue, sensor fusion, authenticity, adulteration, regression, calibration, traceability.

---

## I. Introduction

Coconut water is susceptible to adulteration (e.g. added sugar, acids). Direct quantification of sugar, citric acid, and ascorbic acid typically requires laboratory assays. An E-Tongue provides an indirect route: low-cost sensors (pH, TDS, temperature, turbidity) are combined via sensor fusion and a calibrated model to estimate these constituents and flag out-of-range (adulterated) batches. This document outlines the methodology, calibration modelling, mathematical formulation, and industrial relevance of the system implemented in the Ceylon Coco pipeline (Phases 1–6).

---

## II. Methodology

### A. E-Tongue Setup

- **Sensors:** pH, TDS (total dissolved solids), temperature, turbidity. These are readily available, low-cost, and robust for factory or field use.
- **Hardware:** ESP32 (or equivalent) reads sensors; 3× averaging and simple threshold checks for out-of-range alerts (buzzer). Data are sent via Serial or WiFi to a Raspberry Pi or local PC.
- **Robotic / automation integration (optional):** Cleaning and stabilisation steps (rinse, dry, stabilise) can be automated so the E-Tongue operates in a repeatable cycle (Phase 4). The state machine (READY → sampling → processing → cleaning) ensures consistent conditions across runs.

### B. Sensor Choice

- **pH:** Strongly correlated with organic acid content and fermentation; useful for citric/ascorbic and authenticity.
- **TDS:** Reflects dissolved solids (salts, sugars, acids); complementary to pH.
- **Temperature:** Compensates sensor drift and normalises readings.
- **Turbidity:** Indicates particulates or adulteration that change clarity.

No direct electrochemical sensors for sucrose, citric acid, or ascorbic acid are used; quantification is indirect via regression on the above four inputs after fusion.

### C. Calibration Protocol

1. Prepare controlled samples (e.g. 20–50) with known sugar, citric acid, and ascorbic acid (e.g. by formulation or lab assay).
2. Under fixed temperature and stirring conditions, record pH, TDS, temperature, and turbidity for each sample.
3. Build a regression model (e.g. multiple linear regression or ridge regression) from the fused feature vector to predicted sugar %, citric %, and ascorbic %.
4. Define natural ranges \([L_k, U_k]\) for authentic coconut water for each constituent \(k\).
5. In production, compare model outputs to these ranges to assign *Authentic* or *Adulterated*.

---

## III. Calibration Modelling

Controlled samples map measured variables to known sugar, citric, and ascorbic levels. A representative **reference table** (replace with actual calibration data) is given below. Each row is one calibration sample; the model is trained to predict the last three columns from the first four.

| Sample ID | pH   | TDS (ppm) | Temp (°C) | Turbidity (NTU) | Sugar (%) | Citric (%) | Ascorbic (%) |
|-----------|------|-----------|-----------|-----------------|-----------|------------|---------------|
| C01       | 5.40 | 420       | 25.0      | 2.1             | 2.0       | 0.08       | 0.02          |
| C02       | 5.35 | 450       | 25.0      | 2.5             | 2.5       | 0.10       | 0.025         |
| C03       | 5.50 | 380       | 25.0      | 1.8             | 1.5       | 0.06       | 0.015         |
| …         | …    | …         | …         | …               | …         | …          | …             |

*Table I. Example calibration reference points (expand to 20–50 samples). Real values must be obtained from your calibration runs.*

The regression model (Phase 3) is trained on such a table; the pipeline (Phase 2) applies filtering and moving average to raw sensor streams before extracting the feature vector used as model input.

---

## IV. Mathematical Formulation

### A. Feature Vector

After sensor fusion (filtering, moving average, baseline normalisation), the feature vector for a single reading is:

\[
\mathbf{x} = [\text{pH},\ \text{TDS},\ \text{T},\ \text{turbidity}]^T \in \mathbb{R}^4.
\]

(Additional derived features can be included if used in the trained model.)

### B. Regression Equations

For each constituent \(k \in \{\text{sugar},\ \text{citric},\ \text{ascorbic}\}\), a linear model is assumed (replace with your model form if different):

\[
\hat{y}_k = \mathbf{w}_k^T \mathbf{x} + b_k.
\]

Coefficients \(\mathbf{w}_k\) and \(b_k\) are obtained by least-squares (or regularised regression) on the calibration table. The pipeline outputs predicted sugar %, citric %, and ascorbic %.

### C. Authenticity Condition

Given natural ranges \([L_k, U_k]\) for authentic coconut water:

\[
\text{Authentic} \quad \Leftrightarrow \quad L_k \leq \hat{y}_k \leq U_k \quad \text{for all } k.
\]

If any \(\hat{y}_k\) falls outside \([L_k, U_k]\), the batch is classified as *Adulterated*. Thresholds \(L_k, U_k\) are set from literature or from the empirical range of the calibration set for known-authentic samples.

---

## V. Innovation Justification and Industrial Impact

### A. Innovation

- **Indirect quantification:** Sugar, citric acid, and ascorbic acid are estimated from pH, TDS, temperature, and turbidity via regression—no dedicated sugar/citric/ascorbic sensors.
- **Sensor fusion + regression:** Combining multiple low-cost sensors with a single calibrated model improves robustness and keeps the system deployable in factory or field settings.
- **Industrial applicability:** The same stack runs offline (factory) for real-time detection and online (cloud) for aggregation, dashboards, and traceability.

### B. Industrial Impact

- **Traceability:** Every batch can be logged (readings, predictions, authenticity) in a central DB and linked to time and device.
- **Consumer transparency:** Public dashboards (daily/weekly/monthly aggregates, authenticity badge, ingredient summary) build trust.
- **Adulteration risk reduction:** Automated classification and alerts (e.g. Alerts and SystemLogs when status is adulterated or sensors out-of-range) support rapid response.
- **Scalability and offline-first design:** Detection works without connectivity; data are uploaded when online, so the system scales from single-site to multi-site without blocking local operation.

---

## References

[1] *(Add reference to E-Tongue / electronic tongue applications in food.)*  
[2] *(Add reference to coconut water composition and adulteration.)*  
[3] *(Add reference to sensor fusion or multi-sensor regression in beverages.)*

---

*This document is the Phase 6.10 research documentation outline. Replace placeholders and add references for publication or thesis use.*
