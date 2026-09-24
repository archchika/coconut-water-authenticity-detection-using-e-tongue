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

/** GET /api/daily/readings/ — row for Quality page table */
export interface DailyReadingRow {
  id: number;
  reading: number;
  date: string;
  time: string;
  ph: number;
  predicted_sugar: number;
  predicted_citric: number;
  predicted_ascorbic: number;
  authenticity_status: string;
  confidence: number | null;
  sample_id?: string | null;
  sample_type?: string | null;
  lab_ph?: number | null;
  lab_sugar_pct?: number | null;
  lab_citric_pct?: number | null;
  lab_ascorbic_pct?: number | null;
}

/** GET /api/validation/summary/ — June 30 prototype validation */
export interface ValidationSummaryResponse {
  validation_date: string;
  sample_count: number;
  natural_count: number;
  artificial_count: number;
  overall_accuracy_pct: number;
  ph_accuracy_pct: number;
  ph_mae: number;
  classification_accuracy_pct: number;
  parameters: Record<string, { mape_pct: number; accuracy_pct: number }>;
}

/** POST /api/predict/ — ML inference from sensor inputs */
export interface MLPredictResponse {
  pH: number;
  tds: number;
  temperature: number;
  turbidity: number;
  predicted_sugar: number;
  predicted_citric: number;
  predicted_ascorbic: number;
  authenticity_status: "authentic" | "adulterated";
}

/** POST /api/predict-batch/ — three readings after fusion + ML */
export interface MLPredictBatchResponse {
  readings: MLPredictResponse[];
  fused_sensors: Array<{
    pH: number;
    tds: number;
    temperature: number;
    turbidity: number;
  }>;
  average: MLPredictResponse;
}

export type RobotStage =
  | "initial_position"
  | "detection_station"
  | "cleaning_station"
  | "drying_station";

/** GET /api/esp32-live/ — live buffer, robot stage, and sensor values */
export interface Esp32LiveResponse {
  buffered_count: number;
  required_count: number;
  buffered_readings?: Array<{
    pH: number;
    tds: number;
    temperature: number;
    turbidity: number;
    predicted_sugar?: number;
    predicted_citric?: number;
    predicted_ascorbic?: number;
    authenticity_status?: string;
    source_device_id?: string | null;
  }>;
  current: {
    pH: number;
    tds: number;
    temperature: number;
    turbidity: number;
    source_device_id?: string | null;
  } | null;
  latest_saved: {
    id: number;
    timestamp: string;
    pH: number;
    tds: number;
    temperature: number;
    turbidity: number;
    source_device_id: string | null;
  } | null;
  robot_status: {
    stage: RobotStage;
    source_device_id: string | null;
    updated_at: string;
  } | null;
  /** Last rinse-station sensor snapshot for cleaning verification */
  latest_cleaning?: {
    pH: number;
    tds: number;
    temperature: number;
    turbidity: number;
    source_device_id?: string | null;
    updated_at?: string;
  } | null;
  completed_batch?: {
    readings: Array<{
      pH: number;
      tds: number;
      temperature: number;
      turbidity: number;
      predicted_sugar?: number;
      predicted_citric?: number;
      predicted_ascorbic?: number;
      authenticity_status?: string;
      confidence?: number;
    }>;
    average: {
      pH: number;
      tds: number;
      temperature: number;
      turbidity: number;
      predicted_sugar?: number;
      predicted_citric?: number;
      predicted_ascorbic?: number;
      authenticity_status?: string;
      confidence?: number;
    };
    timestamp?: string;
    device_id?: string;
  } | null;
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
