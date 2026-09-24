/**
 * Allowed sensor windows after cleaning (distilled rinse + dry + stabilise).
 * Current live reading matches if it falls inside each range.
 */
export interface CleaningSensorState {
  ph: number;
  tds: number;
  turbidity: number;
  temperature: number;
}

export interface CleaningRange {
  min: number;
  max: number;
}

export const cleaningSensorKeys: Array<keyof CleaningSensorState> = [
  "ph",
  "tds",
  "turbidity",
  "temperature",
];

export function rangeMidpoint(range: CleaningRange): number {
  return (range.min + range.max) / 2;
}

/** Permanent (expected) windows for the cleaning verification chart. */
export const cleaningTargetRange: Record<keyof CleaningSensorState, CleaningRange> = {
  ph: { min: 5.0, max: 7.0 },
  tds: { min: 0, max: 40 },
  turbidity: { min: 1600, max: 1800 },
  temperature: { min: 27.0, max: 31.0 },
};

/** Midpoint of each window — used to draw the grey bar height. */
export const cleaningInitialState: CleaningSensorState = {
  ph: rangeMidpoint(cleaningTargetRange.ph),
  tds: rangeMidpoint(cleaningTargetRange.tds),
  turbidity: rangeMidpoint(cleaningTargetRange.turbidity),
  temperature: rangeMidpoint(cleaningTargetRange.temperature),
};

export const cleaningSensorLabels: Record<keyof CleaningSensorState, string> = {
  ph: "pH",
  tds: "TDS (ppm)",
  turbidity: "Turbidity",
  temperature: "Temperature (°C)",
};

/** Two bar colours for the cleaning verification chart (same scheme as Natural vs Average). */
export const cleaningChartColors = {
  permanent: "#94a3b8",
  current: "#22c55e",
} as const;

export function formatCleaningRange(range: CleaningRange): string {
  const fmt = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1));
  return `${fmt(range.min)}–${fmt(range.max)}`;
}

export function isWithinRange(value: number, range: CleaningRange): boolean {
  return value >= range.min && value <= range.max;
}

export function evaluateCleaningStatus(current: CleaningSensorState): {
  finished: boolean;
  perSensor: Record<keyof CleaningSensorState, boolean>;
} {
  const perSensor = {} as Record<keyof CleaningSensorState, boolean>;
  for (const key of cleaningSensorKeys) {
    perSensor[key] = isWithinRange(current[key], cleaningTargetRange[key]);
  }
  return {
    finished: cleaningSensorKeys.every((k) => perSensor[k]),
    perSensor,
  };
}
