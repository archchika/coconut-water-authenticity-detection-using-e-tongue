/**
 * Phase 6.1 — API client for Django backend.
 * Uses axios; base URL from VITE_API_BASE_URL (defaults to same origin /api).
 */
import axios, { AxiosInstance, AxiosError } from "axios";
import type { AggregationResponse, ApiError, SensorReadingItem, PredictionItem, AlertItem, SystemLogItem } from "./types";

const baseURL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  (typeof window !== "undefined" ? "" : "http://localhost:8000");
const apiPrefix = baseURL ? `${baseURL}/api` : "/api";

const client: AxiosInstance = axios.create({
  baseURL: apiPrefix,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

/** Attach auth token for upload/admin requests (Phase 5.7). */
export function setAuthToken(token: string | null): void {
  if (token) {
    client.defaults.headers.common["Authorization"] = `Token ${token}`;
  } else {
    delete client.defaults.headers.common["Authorization"];
  }
}

/** GET /api/daily/?date=YYYY-MM-DD */
export async function fetchDaily(date: string): Promise<AggregationResponse> {
  const { data } = await client.get<AggregationResponse>("/daily/", {
    params: { date },
  });
  return data;
}

/** GET /api/weekly/?year=YYYY&week=W */
export async function fetchWeekly(
  year: number,
  week: number
): Promise<AggregationResponse> {
  const { data } = await client.get<AggregationResponse>("/weekly/", {
    params: { year, week },
  });
  return data;
}

/** GET /api/monthly/?year=YYYY&month=M */
export async function fetchMonthly(
  year: number,
  month: number
): Promise<AggregationResponse> {
  const { data } = await client.get<AggregationResponse>("/monthly/", {
    params: { year, month },
  });
  return data;
}

/** POST /api/auth/token/ — obtain token for admin/upload (Phase 6.5). */
export async function login(username: string, password: string): Promise<{ token: string }> {
  const { data } = await client.post<{ token: string }>("/auth/token/", { username, password });
  return data;
}

/** Phase 6.5 — GET /api/readings/?date_from=&date_to=&limit= */
export async function fetchReadings(params: {
  date_from?: string;
  date_to?: string;
  limit?: number;
}): Promise<SensorReadingItem[]> {
  const { data } = await client.get<SensorReadingItem[]>("/readings/", { params });
  return data;
}

/** Phase 6.5 — GET /api/predictions/?date_from=&date_to=&status=&limit= */
export async function fetchPredictions(params: {
  date_from?: string;
  date_to?: string;
  status?: string;
  limit?: number;
}): Promise<PredictionItem[]> {
  const { data } = await client.get<PredictionItem[]>("/predictions/", { params });
  return data;
}

/** Phase 6.6 — GET /api/alerts/?date_from=&date_to=&type=&resolved=&limit= */
export async function fetchAlerts(params: {
  date_from?: string;
  date_to?: string;
  type?: string;
  resolved?: boolean;
  limit?: number;
}): Promise<AlertItem[]> {
  const { data } = await client.get<AlertItem[]>("/alerts/", { params });
  return data;
}

/** Phase 6.6 — PATCH /api/alerts/<id>/ — set resolved. */
export async function resolveAlert(id: number, resolved: boolean): Promise<AlertItem> {
  const { data } = await client.patch<AlertItem>(`/alerts/${id}/`, { resolved });
  return data;
}

/** Phase 6.6 — GET /api/logs/?date_from=&date_to=&level=&component=&search=&limit= */
export async function fetchLogs(params: {
  date_from?: string;
  date_to?: string;
  level?: string;
  component?: string;
  search?: string;
  limit?: number;
}): Promise<SystemLogItem[]> {
  const { data } = await client.get<SystemLogItem[]>("/logs/", { params });
  return data;
}

/** Normalise API error message from Django / DRF (error, detail, non_field_errors). */
export function getApiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const ax = err as AxiosError<ApiError>;
    const body = ax.response?.data as ApiError | undefined;
    if (body?.error) return body.error;
    if (body?.detail) {
      if (typeof body.detail === "string") return body.detail;
      if (Array.isArray(body.detail) && body.detail[0]) return body.detail[0];
    }
    if (body?.non_field_errors?.length) return body.non_field_errors[0];
  }
  return err instanceof Error ? err.message : "Request failed";
}

export default client;
