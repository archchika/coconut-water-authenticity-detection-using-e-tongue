/** Natural ranges — aligned with backend ml_inference.py (pH + composition) */
const NATURAL_RANGES = {
  ph: [4.7, 6.32] as const,
  sugar: [1.8, 7.0] as const,
  citric: [0.04, 0.15] as const,
  ascorbic: [0.0008, 0.0035] as const,
};

const PROTOTYPE_MAX = 0.95;
const PROTOTYPE_MIN = 0.52;

function inRange(value: number, low: number, high: number): boolean {
  return value >= low && value <= high;
}

function rangeFitScore(value: number, low: number, high: number): number {
  if (!inRange(value, low, high)) return 0;
  const mid = (low + high) / 2;
  const halfSpan = (high - low) / 2;
  if (halfSpan <= 0) return 1;
  return Math.max(0, 1 - Math.abs(value - mid) / halfSpan);
}

function violationSeverity(value: number, low: number, high: number): number {
  if (inRange(value, low, high)) return 0;
  const span = Math.max(high - low, 1e-12);
  const excess = value < low ? low - value : value - high;
  return Math.min(1, excess / (span * 0.5));
}

function isAuthentic(
  sugar: number,
  citric: number,
  ascorbic: number,
  ph?: number | null,
): boolean {
  const compositionOk =
    inRange(sugar, ...NATURAL_RANGES.sugar) &&
    inRange(citric, ...NATURAL_RANGES.citric) &&
    inRange(ascorbic, ...NATURAL_RANGES.ascorbic);
  if (ph == null) return compositionOk;
  return compositionOk && inRange(ph, ...NATURAL_RANGES.ph);
}

/** Prototype confidence (0.52–0.95) — mirrors backend compute_confidence. */
export function computeConfidence(
  sugar: number,
  citric: number,
  ascorbic: number,
  ph?: number | null,
): number {
  const params: Array<readonly [number, number, number]> = [
    [sugar, ...NATURAL_RANGES.sugar],
    [citric, ...NATURAL_RANGES.citric],
    [ascorbic, ...NATURAL_RANGES.ascorbic],
  ];
  if (ph != null) {
    params.unshift([ph, ...NATURAL_RANGES.ph]);
  }

  let raw: number;
  if (!isAuthentic(sugar, citric, ascorbic, ph)) {
    const severities = params.map(([v, lo, hi]) => violationSeverity(v, lo, hi));
    const avgSeverity = severities.reduce((a, b) => a + b, 0) / severities.length;
    const failingCount = severities.filter((s) => s > 0).length;
    raw = 0.58 + 0.3 * avgSeverity + Math.max(0, failingCount - 1) * 0.06;
  } else {
    const fits = params.map(([v, lo, hi]) => rangeFitScore(v, lo, hi));
    const avgFit = fits.reduce((a, b) => a + b, 0) / fits.length;
    const minFit = Math.min(...fits);
    raw = 0.55 + 0.33 * (0.6 * avgFit + 0.4 * minFit);
  }

  return Math.round(Math.max(PROTOTYPE_MIN, Math.min(PROTOTYPE_MAX, raw)) * 10000) / 10000;
}

export function resolveConfidence(
  stored: number | null | undefined,
  sugar: number | null,
  citric: number | null,
  ascorbic: number | null,
  ph?: number | null,
): number | null {
  if (stored != null) return stored;
  if (sugar == null || citric == null || ascorbic == null) return null;
  return computeConfidence(sugar, citric, ascorbic, ph);
}
