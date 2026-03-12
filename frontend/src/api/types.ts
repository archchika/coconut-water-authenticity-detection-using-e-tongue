/**
 * Types for Django API responses (Phase 6.1).
 * Matches backend readings/aggregation.py and API views.
 */

export interface AggregationAverages {
  ph: number | null;
  tds: number | null;
  temperature: number | null;
  turbidity: number | null;
  predicted_sugar: number | null;
  predicted_citric: number | null;
  predicted_ascorbic: number | null;
}

export interface AggregationAuthenticity {
  authentic: number;
  adulterated: number;
}

export interface AggregationResponse {
  count: number;
  averages: AggregationAverages;
  authenticity: AggregationAuthenticity;
  status: "authentic" | "adulterated";
  period: string;
  period_type: "daily" | "weekly" | "monthly";
}

export interface ApiError {
  error?: string;
  detail?: string | string[] | Record<string, string[]>;
  non_field_errors?: string[];
}

/** Phase 6.5 — GET /api/readings/ list item */
export interface SensorReadingItem {
  id: number;
  timestamp: string;
  ph: number;
  tds: number;
  temperature: number;
  turbidity: number;
  source_device_id: string | null;
}

/** Phase 6.5 — GET /api/predictions/ list item */
export interface PredictionItem {
  id: number;
  reading: number;
  timestamp: string;
  predicted_sugar: number;
  predicted_citric: number;
  predicted_ascorbic: number;
  authenticity_status: string;
  confidence: number | null;
}

/** Phase 6.6 — GET /api/alerts/ list item */
export interface AlertItem {
  id: number;
  timestamp: string;
  type: string;
  message: string;
  reading: number | null;
  resolved: boolean;
}

/** Phase 6.6 — GET /api/logs/ list item */
export interface SystemLogItem {
  id: number;
  timestamp: string;
  level: string;
  component: string;
  message: string;
  metadata: Record<string, unknown>;
}
