/**
 * Natural coconut water reference ranges (DOST PH study + literature).
 * Used for Natural vs Our Product comparison on the Quality page.
 */
export const naturalReference = {
  source: "DOST PH study (natural coconut water) + literature",
  parameters: {
    ph: { min: 4.7, max: 6.32, mean: 5.44, unit: "pH", label: "pH" },
    predicted_sugar: {
      min: 1.8,
      max: 7,
      mean: 4.4,
      unit: "%",
      label: "Sugar %",
      note: "From brix (natural coconut water)",
    },
    predicted_citric: { min: 0.04, max: 0.15, mean: 0.08, unit: "%", label: "Citric acid %" },
    predicted_ascorbic: {
      min: 0.00015,
      max: 0.00035,
      mean: 0.00025,
      unit: "%",
      label: "Ascorbic acid %",
      note: "1.80-2.92 µg/mL (natural coconut water)",
    },
  },
  dostStats: {
    glucose: { min: 0.24, max: 35.64, mean: 15.59, unit: "mg/100 mL" },
    brix: { min: 1.8, max: 6.73, mean: 4.36, unit: "°Brix" },
    potassium: { min: 16.37, max: 76.22, mean: 52.18, unit: "mg/100 mL" },
    calcium: { min: 0.75, max: 8.48, mean: 4.22, unit: "mg/100 mL" },
    sodium: { min: 1.3, max: 8.7, mean: 4.19, unit: "mg/100 mL" },
    chloride: { min: 14.67, max: 56.98, mean: 34.72, unit: "mg/100 mL" },
  },
} as const;
