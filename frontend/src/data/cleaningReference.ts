/**
 * Fixed sensor baseline after cleaning cycle (distilled rinse + dry + stabilise).
 * Aligned with firmware PH_BASELINE (6.8–7.2) and sensor_fusion pipeline baseline.
 */
export interface CleaningSensorState {
  ph: number;
  tds: number;
  turbidity: number;
  temperature: number;
}

/** Expected readings when the e-tongue is clean and ready for the next sample. */
export const cleaningInitialState: CleaningSensorState = {
  ph: 7.0,
  tds: 10,
  turbidity: 1.0,
  temperature: 25.0,
};

/** Allowed deviation from initial state before re-cleaning is required. */
export const cleaningTolerance: CleaningSensorState = {
  ph: 0.2,
  tds: 30,
  turbidity: 2,
  temperature: 2,
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

export function isWithinTolerance(
  initial: number,
  current: number,
  tolerance: number
): boolean {
  return Math.abs(current - initial) <= tolerance;
}

export function evaluateCleaningStatus(current: CleaningSensorState): {
  finished: boolean;
  perSensor: Record<keyof CleaningSensorState, boolean>;
} {
  const keys = Object.keys(cleaningInitialState) as (keyof CleaningSensorState)[];
  const perSensor = {} as Record<keyof CleaningSensorState, boolean>;
  for (const key of keys) {
    perSensor[key] = isWithinTolerance(
      cleaningInitialState[key],
      current[key],
      cleaningTolerance[key]
    );
  }
  return {
    finished: keys.every((k) => perSensor[k]),
    perSensor,
  };
}
