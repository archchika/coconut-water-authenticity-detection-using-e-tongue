import { Link } from "react-router-dom";

/**
 * Phase 6.4 — Methodology page (linked from ingredient transparency summary).
 * Full content can be expanded in Phase 6.10 (research documentation).
 */
export default function Methodology() {
  return (
    <div className="methodology-page">
      <h1>Methodology</h1>
      <p>
        Our coconut water authenticity and ingredient estimates are produced using an <strong>E-Tongue</strong> (electronic tongue)
        system: multi-sensor readings (pH, TDS, temperature, turbidity) are fused and fed into a calibrated model that predicts
        sugar, citric acid, and ascorbic acid levels. Predictions are compared to natural ranges to classify each batch as
        <strong> authentic</strong> or <strong> adulterated</strong>.
      </p>
      <p>
        Sensors are calibrated against controlled samples. The full methodology, calibration protocol, mathematical formulation,
        and industrial impact are documented in <strong>docs/research/METHODOLOGY.md</strong> (IEEE-style research outline) in the project repository.
      </p>
      <p>
        <Link to="/">← Back to dashboard</Link>
      </p>
    </div>
  );
}
