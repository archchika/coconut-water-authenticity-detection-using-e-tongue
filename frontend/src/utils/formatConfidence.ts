/** Format stored confidence (0–1) for display as a percentage. */
export function formatConfidence(value: number | null | undefined): string {
  if (value == null) return "\u2014";
  return `${Math.round(value * 100)}%`;
}

/** Confidence as integer percent for exports (empty string if missing). */
export function confidencePercent(value: number | null | undefined): string {
  if (value == null) return "";
  return `${Math.round(value * 100)}%`;
}
