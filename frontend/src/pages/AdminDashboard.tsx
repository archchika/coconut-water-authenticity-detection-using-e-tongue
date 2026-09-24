/**
 * Phase 6.5 / 6.6 — Admin dashboard: raw data, alerts (with resolve), system logs.
 * Adulteration alert: sound + blinking indicator when adulterated sample identified.
 * Review: modal with per-parameter graphs (pH, sugar, citric, ascorbic).
 */
import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useLocation } from "react-router-dom";
import {
  PieChart,
  Pie,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import {
  fetchReadings,
  fetchPredictions,
  fetchLogs,
  fetchDaily,
  fetchWeekly,
  fetchMonthly,
  fetchEsp32Live,
  getApiErrorMessage,
} from "../api/client";
import jsPDF from "jspdf";
import * as XLSX from "xlsx";
import type {
  AggregationResponse,
  SensorReadingItem,
  PredictionItem,
  SystemLogItem,
  Esp32LiveResponse,
  RobotStage,
} from "../api/types";
import { format, getISOWeek, startOfWeek, endOfWeek, startOfMonth, endOfMonth, addWeeks } from "date-fns";
import { formatConfidence, confidencePercent } from "../utils/formatConfidence";
import { resolveConfidence } from "../utils/computeConfidence";
import {
  cleaningSensorLabels,
  cleaningChartColors,
  cleaningSensorKeys,
  cleaningTargetRange,
  formatCleaningRange,
  rangeMidpoint,
  evaluateCleaningStatus,
  type CleaningSensorState,
} from "../data/cleaningReference";

/** Max rows fetched for PDF/CSV export (June 30 validation = 200). */
const EXPORT_FETCH_LIMIT = 500;

function resolvePeriodRange(
  periodType: "day" | "week" | "month",
  selectedDate: string,
  selectedYear: number,
  selectedWeek: number,
  selectedMonth: number,
): { dateFrom: string; dateTo: string } {
  if (periodType === "day") {
    return { dateFrom: selectedDate, dateTo: selectedDate };
  }
  if (periodType === "week") {
    const jan4 = new Date(selectedYear, 0, 4);
    const mondayOfWeek1 = startOfWeek(jan4, { weekStartsOn: 1 });
    const targetMonday = addWeeks(mondayOfWeek1, selectedWeek - 1);
    return {
      dateFrom: format(targetMonday, "yyyy-MM-dd"),
      dateTo: format(endOfWeek(targetMonday, { weekStartsOn: 1 }), "yyyy-MM-dd"),
    };
  }
  const start = startOfMonth(new Date(selectedYear, selectedMonth - 1));
  const end = endOfMonth(new Date(selectedYear, selectedMonth - 1));
  return {
    dateFrom: format(start, "yyyy-MM-dd"),
    dateTo: format(end, "yyyy-MM-dd"),
  };
}

function getPeriodFileBase(prefix: string, periodType: "day" | "week" | "month", selectedDate: string, selectedYear: number, selectedWeek: number, selectedMonth: number): string {
  if (periodType === "day") return `${prefix}-${selectedDate}`;
  if (periodType === "week") return `${prefix}-${selectedYear}-W${selectedWeek}`;
  return `${prefix}-${selectedYear}-${String(selectedMonth).padStart(2, "0")}`;
}

function downloadCsvFile(filename: string, rows: string[][]): void {
  const csv = rows
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob(["\ufeff", csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function downloadExcelFile(filename: string, sheets: { name: string; rows: string[][] }[]): void {
  const wb = XLSX.utils.book_new();
  for (const sheet of sheets) {
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(sheet.rows), sheet.name);
  }
  XLSX.writeFile(wb, filename);
}

function buildAggregationSummaryRows(agg: AggregationResponse, periodLabel: string): string[][] {
  return [
    ["Coconut Water Quality Report"],
    ["Period", periodLabel],
    ["Period type", agg.period_type],
    [],
    ["Summary"],
    ["Total readings", String(agg.count)],
    ["Authentic", String(agg.authenticity.authentic)],
    ["Adulterated", String(agg.authenticity.adulterated)],
    ["Overall status", agg.status],
    [],
    ["Averages"],
    ["pH", agg.averages.ph != null ? String(agg.averages.ph) : ""],
    ["TDS", agg.averages.tds != null ? String(agg.averages.tds) : ""],
    ["Temperature", agg.averages.temperature != null ? String(agg.averages.temperature) : ""],
    ["Turbidity", agg.averages.turbidity != null ? String(agg.averages.turbidity) : ""],
    ["Sugar %", agg.averages.predicted_sugar != null ? String(agg.averages.predicted_sugar) : ""],
    ["Citric %", agg.averages.predicted_citric != null ? String(agg.averages.predicted_citric) : ""],
    ["Ascorbic %", agg.averages.predicted_ascorbic != null ? String(agg.averages.predicted_ascorbic) : ""],
  ];
}

function sensorReadingExportRows(readings: SensorReadingItem[]): string[][] {
  const headers = ["ID", "Date", "Time", "pH", "TDS", "Temperature", "Turbidity", "Device"];
  const rows: string[][] = [headers];
  for (const r of readings) {
    const dt = new Date(r.timestamp);
    rows.push([
      String(r.id),
      format(dt, "yyyy-MM-dd"),
      format(dt, "HH:mm"),
      String(r.ph),
      String(r.tds),
      String(r.temperature),
      String(r.turbidity),
      r.source_device_id ?? "",
    ]);
  }
  return rows;
}

function predictionExportRows(predictions: PredictionItem[], readingById: Map<number, SensorReadingItem>): string[][] {
  const headers = ["ID", "Reading", "Date", "Time", "pH", "Sugar %", "Citric %", "Ascorbic %", "Status", "Confidence"];
  const rows: string[][] = [headers];
  for (const p of predictions) {
    const r = readingById.get(p.reading);
    const dt = new Date(p.timestamp);
    rows.push([
      String(p.id),
      String(p.reading),
      format(dt, "yyyy-MM-dd"),
      format(dt, "HH:mm"),
      r?.ph != null ? String(r.ph) : "",
      String(p.predicted_sugar),
      String(p.predicted_citric),
      String(p.predicted_ascorbic),
      p.authenticity_status === "authentic" ? "Authentic" : "Adulterated",
      p.confidence != null ? confidencePercent(p.confidence) : "",
    ]);
  }
  return rows;
}

/** Typical ranges for coconut water (for review comparison). */
const TYPICAL_RANGES = {
  ph: { min: 4.5, max: 5.5 },
  sugar: { min: 4, max: 6 },
  citric: { min: 0.08, max: 0.15 },
  ascorbic: { min: 0.05, max: 0.12 },
};

type ReadingData = {
  ph: number | null;
  citric: number | null;
  ascorbic: number | null;
  sugar: number | null;
  authentic?: boolean;
  confidence?: number | null;
};

type LiveReadingSlot = ReadingData & { tds?: number; temperature?: number; turbidity?: number };

type LiveReadingsState = [LiveReadingSlot | null, LiveReadingSlot | null, LiveReadingSlot | null];

function predictionToLiveSlot(pred: PredictionItem, reading: SensorReadingItem): LiveReadingSlot {
  return {
    ph: reading.ph,
    citric: pred.predicted_citric,
    ascorbic: pred.predicted_ascorbic,
    sugar: pred.predicted_sugar,
    authentic: pred.authenticity_status === "authentic",
    confidence: resolveConfidence(
      pred.confidence,
      pred.predicted_sugar,
      pred.predicted_citric,
      pred.predicted_ascorbic,
      reading.ph,
    ),
    tds: reading.tds,
    temperature: reading.temperature,
    turbidity: reading.turbidity,
  };
}

/** Sensor-only slot while ESP32 batch is still collecting (ML runs after 3rd reading). */
function bufferedToLiveSlot(raw: NonNullable<Esp32LiveResponse["buffered_readings"]>[number]): LiveReadingSlot {
  const sugar = raw.predicted_sugar ?? null;
  const citric = raw.predicted_citric ?? null;
  const ascorbic = raw.predicted_ascorbic ?? null;
  return {
    ph: raw.pH,
    citric,
    ascorbic,
    sugar,
    authentic:
      raw.authenticity_status === "authentic"
        ? true
        : raw.authenticity_status === "adulterated"
          ? false
          : undefined,
    confidence: resolveConfidence(undefined, sugar, citric, ascorbic, raw.pH),
    tds: raw.tds,
    temperature: raw.temperature,
    turbidity: raw.turbidity,
  };
}

/** Build First/Second/Third slots from esp32-live while batch is collecting. */
function buildBatchSlots(live: Esp32LiveResponse): LiveReadingsState {
  const partial: LiveReadingsState = [null, null, null];
  const buffered = live.buffered_readings ?? [];
  for (let i = 0; i < live.buffered_count && i < 3; i++) {
    let raw = buffered[i];
    // Prefer buffer slot; fall back to live.current for any missing slot (esp. reading 1).
    if (!raw && live.current) {
      raw = {
        pH: live.current.pH,
        tds: live.current.tds,
        temperature: live.current.temperature,
        turbidity: live.current.turbidity,
      };
    }
    if (raw) partial[i] = bufferedToLiveSlot(raw);
  }
  // Guarantee slot 0 while a batch is open and we have a current snapshot.
  if (live.buffered_count >= 1 && !partial[0] && live.current) {
    partial[0] = bufferedToLiveSlot({
      pH: live.current.pH,
      tds: live.current.tds,
      temperature: live.current.temperature,
      turbidity: live.current.turbidity,
    });
  }
  return partial;
}

/** Finished 3-reading batch from esp32-live (includes ML + authenticity). */
function buildCompletedBatchSlots(
  batch: NonNullable<Esp32LiveResponse["completed_batch"]>,
): LiveReadingsState {
  const slots: LiveReadingsState = [null, null, null];
  batch.readings.slice(0, 3).forEach((raw, i) => {
    slots[i] = bufferedToLiveSlot(raw);
  });
  return slots;
}

function completedBatchToSummary(
  batch: NonNullable<Esp32LiveResponse["completed_batch"]>,
): ReadingData {
  const avg = batch.average;
  return {
    ph: avg.pH ?? null,
    citric: avg.predicted_citric ?? null,
    ascorbic: avg.predicted_ascorbic ?? null,
    sugar: avg.predicted_sugar ?? null,
    authentic:
      avg.authenticity_status === "authentic"
        ? true
        : avg.authenticity_status === "adulterated"
          ? false
          : undefined,
    confidence: avg.confidence ?? null,
  };
}

function rawToLiveSlot(raw: {
  pH: number;
  tds: number;
  temperature: number;
  turbidity: number;
}): LiveReadingSlot {
  return {
    ph: raw.pH,
    citric: null,
    ascorbic: null,
    sugar: null,
    tds: raw.tds,
    temperature: raw.temperature,
    turbidity: raw.turbidity,
  };
}

function averageReadings(readings: (ReadingData | null)[]): ReadingData {
  const valid = readings.filter(
    (x): x is ReadingData =>
      x != null && x.ph != null && x.citric != null && x.ascorbic != null && x.sugar != null
  );
  if (valid.length === 0) return { ph: null, citric: null, ascorbic: null, sugar: null, confidence: null };
  const withConf = valid.filter((x) => x.confidence != null);
  const avgSugar = valid.reduce((s, x) => s + (x.sugar ?? 0), 0) / valid.length;
  const avgCitric = valid.reduce((s, x) => s + (x.citric ?? 0), 0) / valid.length;
  const avgAscorbic = valid.reduce((s, x) => s + (x.ascorbic ?? 0), 0) / valid.length;
  const avgPh = valid.reduce((s, x) => s + (x.ph ?? 0), 0) / valid.length;
  return {
    ph: avgPh,
    citric: avgCitric,
    ascorbic: avgAscorbic,
    sugar: avgSugar,
    confidence:
      withConf.length > 0
        ? withConf.reduce((s, x) => s + (x.confidence ?? 0), 0) / withConf.length
        : resolveConfidence(null, avgSugar, avgCitric, avgAscorbic, avgPh),
  };
}

const EMPTY_READING: ReadingData = { ph: null, citric: null, ascorbic: null, sugar: null };

type SensorSnapshot = {
  pH: number | null;
  tds: number;
  temperature: number;
  turbidity: number;
};

/** Colors for pH, citric acid, ascorbic acid, sugar (dots and charts). */
const PARAM_COLORS = { ph: "#4A90E2", citric: "#F5A623", ascorbic: "#14B8A6", sugar: "#27AE60" };

/** Matches firmware ENABLE_PH_SENSOR=1 — pH on D35 */
const PH_SENSOR_ENABLED = true;

/** Live ESP32 sensor panel — polls backend for TDS, temp, turbidity (pH when enabled). */
function SensorPredictPanel({
  currentSnapshot,
  bufferedCount,
  requiredCount,
  waiting,
}: {
  currentSnapshot: SensorSnapshot | null;
  bufferedCount: number;
  requiredCount: number;
  waiting: boolean;
}) {
  const sensors: { key: keyof SensorSnapshot; label: string; format: (v: number) => string }[] = [
    ...(PH_SENSOR_ENABLED
      ? [{ key: "pH" as const, label: "pH", format: (v: number) => v.toFixed(2) }]
      : []),
    { key: "tds", label: "TDS", format: (v) => v.toFixed(1) },
    { key: "temperature", label: "Temp °C", format: (v) => v.toFixed(1) },
    { key: "turbidity", label: "Turbidity", format: (v) => v.toFixed(2) },
  ];

  return (
    <div className="admin-sensor-predict-panel admin-report-panel">
      <div className="admin-sensor-predict-header">
        <h3 className="admin-report-panel-title">Sensor reading (ESP32 live)</h3>
        {!PH_SENSOR_ENABLED && (
          <span className="admin-sensor-predict-hint">pH sensor not connected</span>
        )}
      </div>

      {waiting && !currentSnapshot && (
        <p className="admin-sensor-predict-wait">Waiting for ESP32 measurement…</p>
      )}

      {bufferedCount > 0 && bufferedCount < requiredCount && (
        <p className="admin-sensor-predict-buffer">
          Receiving batch: {bufferedCount}/{requiredCount}
        </p>
      )}

      <div className="admin-sensor-snapshot-grid">
        {sensors.map(({ key, label, format }) => (
          <div key={String(key)} className="admin-sensor-snapshot-cell">
            <span className="admin-sensor-snapshot-label">{label}</span>
            <span className="admin-sensor-snapshot-value">
              {currentSnapshot && currentSnapshot[key] != null
                ? format(currentSnapshot[key] as number)
                : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** Period selector for first page: Day / Week / Month with date selection. */
function PeriodSelectorBar({
  periodType,
  setPeriodType,
  selectedDate,
  setSelectedDate,
  selectedYear,
  setSelectedYear,
  selectedWeek,
  setSelectedWeek,
  selectedMonth,
  setSelectedMonth,
  onApply,
  onDownloadPdf,
  onDownloadCsv,
  onDownloadExcel,
  loading,
  variant = "dark",
}: {
  periodType: "day" | "week" | "month";
  setPeriodType: (v: "day" | "week" | "month") => void;
  selectedDate: string;
  setSelectedDate: (v: string) => void;
  selectedYear: number;
  setSelectedYear: (v: number) => void;
  selectedWeek: number;
  setSelectedWeek: (v: number) => void;
  selectedMonth: number;
  setSelectedMonth: (v: number) => void;
  onApply: () => void;
  onDownloadPdf: () => void;
  onDownloadCsv: () => void;
  onDownloadExcel: () => void;
  loading: boolean;
  variant?: "dark" | "light";
}) {
  return (
    <div className={`admin-report-period-bar admin-report-period-bar--${variant}`}>
      <label>
        Period:{" "}
        <select value={periodType} onChange={(e) => setPeriodType(e.target.value as "day" | "week" | "month")}>
          <option value="day">Day</option>
          <option value="week">Week</option>
          <option value="month">Month</option>
        </select>
      </label>
      {periodType === "day" && (
        <label>
          Date: <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
        </label>
      )}
      {periodType === "week" && (
        <>
          <label>
            Year: <input type="number" min={2020} max={2030} value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))} />
          </label>
          <label>
            Week: <input type="number" min={1} max={53} value={selectedWeek} onChange={(e) => setSelectedWeek(Number(e.target.value))} />
          </label>
        </>
      )}
      {periodType === "month" && (
        <>
          <label>
            Year: <input type="number" min={2020} max={2030} value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))} />
          </label>
          <label>
            Month: <input type="number" min={1} max={12} value={selectedMonth} onChange={(e) => setSelectedMonth(Number(e.target.value))} />
          </label>
        </>
      )}
      <button type="button" onClick={onApply} disabled={loading}>
        {loading ? "Loading…" : "Apply"}
      </button>
      <span className="admin-download-group">
        <button type="button" onClick={onDownloadPdf} disabled={loading} className="admin-download-pdf-btn">
          PDF
        </button>
        <button type="button" onClick={onDownloadCsv} disabled={loading} className="admin-download-pdf-btn">
          CSV
        </button>
        <button type="button" onClick={onDownloadExcel} disabled={loading} className="admin-download-pdf-btn">
          Excel
        </button>
      </span>
    </div>
  );
}

/** Production report layout: Assembly Lines style (dark theme, Summary + First/Second/Third panels). */
function ProductionReportOverview({
  liveReadings,
  cleaningReading,
  activeReadingIndex,
  bufferedCount,
  requiredCount,
  robotStage,
  completedVerdict,
}: {
  liveReadings: LiveReadingsState;
  cleaningReading: CleaningSensorState | null;
  activeReadingIndex: number;
  bufferedCount: number;
  requiredCount: number;
  robotStage: RobotStage | null;
  completedVerdict: "authentic" | "adulterated" | null;
}) {
  const hasLiveSession = liveReadings.some((r) => r != null);
  const isCollecting = bufferedCount > 0 && bufferedCount < requiredCount;

  const { summary, first, second, third } = useMemo(() => {
    if (isCollecting) {
      const firstSlot = bufferedCount >= 1 && liveReadings[0] ? liveReadings[0] : EMPTY_READING;
      const secondSlot = bufferedCount >= 2 && liveReadings[1] ? liveReadings[1] : EMPTY_READING;
      const thirdSlot = EMPTY_READING;
      return {
        first: firstSlot,
        second: secondSlot,
        third: thirdSlot,
        summary: EMPTY_READING,
      };
    }

    if (hasLiveSession) {
      const firstSlot = liveReadings[0] ?? EMPTY_READING;
      const secondSlot = liveReadings[1] ?? EMPTY_READING;
      const thirdSlot = liveReadings[2] ?? EMPTY_READING;
      const allThree =
        liveReadings[0] != null && liveReadings[1] != null && liveReadings[2] != null;
      return {
        first: firstSlot,
        second: secondSlot,
        third: thirdSlot,
        summary: allThree ? averageReadings(liveReadings) : EMPTY_READING,
      };
    }

    // No live ESP32 session yet — keep panels empty (do not show old DB / sample data).
    return {
      summary: EMPTY_READING,
      first: EMPTY_READING,
      second: EMPTY_READING,
      third: EMPTY_READING,
    };
  }, [liveReadings, hasLiveSession, isCollecting, bufferedCount, requiredCount]);

  const fmt = (v: number | null) => (v != null ? (v < 0.01 ? v.toFixed(4) : v.toFixed(2)) : "\u2014");

  const MetricRow = ({ label, value, color }: { label: string; value: number | null; color: string }) => (
    <div className="admin-report-metric-row">
      <span className="admin-report-metric-dot" style={{ backgroundColor: color }} aria-hidden />
      <span className="admin-report-metric-label">{label}</span>
      <span className="admin-report-metric-value">{fmt(value)}</span>
    </div>
  );

  const ReadingPanel = ({ title, data }: { title: string; data: ReadingData }) => (
    <div className="admin-report-panel admin-report-panel-compact">
      <h3 className="admin-report-panel-title">{title}</h3>
      <MetricRow label="pH" value={data.ph} color={PARAM_COLORS.ph} />
      <MetricRow label="Citric acid %" value={data.citric} color={PARAM_COLORS.citric} />
      <MetricRow label="Ascorbic acid %" value={data.ascorbic} color={PARAM_COLORS.ascorbic} />
      <MetricRow label="Sugar %" value={data.sugar} color={PARAM_COLORS.sugar} />
    </div>
  );

  const paramsPieData = useMemo(() => {
    const s = summary;
    if (s.ph == null && s.citric == null && s.ascorbic == null && s.sugar == null) return [];
    const v = (x: number | null, max: number) => (x != null ? Math.max(0.5, Math.min(100, (x / max) * 100)) : 0);
    return [
      { name: "pH", value: v(s.ph, 7), raw: s.ph, fill: PARAM_COLORS.ph },
      { name: "Citric %", value: v(s.citric ?? 0, 0.2), raw: s.citric ?? 0, fill: PARAM_COLORS.citric },
      { name: "Ascorbic %", value: v(s.ascorbic ?? 0, 0.15), raw: s.ascorbic ?? 0, fill: PARAM_COLORS.ascorbic },
      { name: "Sugar %", value: v(s.sugar ?? 0, 10), raw: s.sugar ?? 0, fill: PARAM_COLORS.sugar },
    ];
  }, [summary]);

  const currentCleaning: CleaningSensorState | null = cleaningReading;

  const cleaningEvaluation = useMemo(() => {
    if (!currentCleaning) return null;
    return evaluateCleaningStatus(currentCleaning);
  }, [currentCleaning]);

  const cleaningChartData = useMemo(() => {
    const chartScale: Record<keyof CleaningSensorState, { min: number; max: number }> = {
      ph: { min: 4.0, max: 7.0 },
      tds: { min: 0, max: 200 },
      turbidity: { min: 0, max: 2000 },
      temperature: { min: 20, max: 35 },
    };
    const norm = (v: number, min: number, max: number) =>
      Math.max(0, Math.min(100, ((v - min) / (max - min || 0.001)) * 100));
    const perSensor = cleaningEvaluation?.perSensor;
    const hasReading = currentCleaning != null;
    return cleaningSensorKeys.map((key) => {
      const target = cleaningTargetRange[key];
      return {
        name: cleaningSensorLabels[key],
        initial: norm(rangeMidpoint(target), chartScale[key].min, chartScale[key].max),
        current: hasReading
          ? norm(currentCleaning[key], chartScale[key].min, chartScale[key].max)
          : 4,
        initialRaw: rangeMidpoint(target),
        rangeLabel: formatCleaningRange(target),
        currentRaw: currentCleaning?.[key] ?? null,
        hasReading,
        matches: hasReading ? (perSensor?.[key] ?? false) : false,
      };
    });
  }, [currentCleaning, cleaningEvaluation]);

  const cleaningChartVerdict = cleaningEvaluation
    ? cleaningEvaluation.finished
      ? "Cleaning finished"
      : "Clean again"
    : "Awaiting sensor reading";

  const robotStages: Array<{ stage: RobotStage; label: string }> = [
    { stage: "initial_position", label: "Initial Position" },
    { stage: "detection_station", label: "Detection Station" },
    { stage: "cleaning_station", label: "Cleaning Station" },
    { stage: "drying_station", label: "Drying Station" },
  ];

  const stepCircleClass = (step: 1 | 2 | 3) => {
    if (!hasLiveSession && !isCollecting) return "";
    const completed = isCollecting ? step <= bufferedCount : liveReadings[step - 1] != null;
    if (activeReadingIndex === step) return "admin-report-step-circle-active";
    if (completed) return "admin-report-step-circle-done";
    return "";
  };

  return (
    <div className="admin-report-dashboard">
      <header className="admin-report-header">
        <h1 className="admin-report-title admin-report-title-white">Coconut Water Authenticity Dashboard</h1>
        <div className="admin-authenticity-choice" role="status">
          <div
            className={`admin-authenticity-choice-card ${
              completedVerdict === "authentic" ? "admin-authenticity-choice-on" : ""
            }`}
          >
            Authentic
          </div>
          <div
            className={`admin-authenticity-choice-card ${
              completedVerdict === "adulterated" ? "admin-authenticity-choice-on-bad" : ""
            }`}
          >
            Adulterated
          </div>
        </div>
      </header>

      <div className="admin-report-panels-wrap">
        <div className="admin-report-step-indicator">
          <div className="admin-report-step-item">
            <div className={`admin-report-step-circle ${stepCircleClass(1)}`}>1</div>
            <span className="admin-report-step-label">First reading</span>
          </div>
          <div className="admin-report-step-connector" />
          <div className="admin-report-step-item">
            <div className={`admin-report-step-circle ${stepCircleClass(2)}`}>2</div>
            <span className="admin-report-step-label">Second reading</span>
          </div>
          <div className="admin-report-step-connector" />
          <div className="admin-report-step-item">
            <div className={`admin-report-step-circle ${stepCircleClass(3)}`}>3</div>
            <span className="admin-report-step-label">Third reading</span>
          </div>
        </div>
        <div className="admin-report-panels-row">
          <ReadingPanel title="First reading" data={first} />
          <ReadingPanel title="Second reading" data={second} />
          <ReadingPanel title="Third reading" data={third} />
          <div className="admin-report-panel admin-report-panel-compact admin-report-summary">
            <h3 className="admin-report-panel-title admin-report-summary-title">Average reading</h3>
            <MetricRow label="pH" value={summary.ph} color={PARAM_COLORS.ph} />
            <MetricRow label="Citric acid %" value={summary.citric} color={PARAM_COLORS.citric} />
            <MetricRow label="Ascorbic acid %" value={summary.ascorbic} color={PARAM_COLORS.ascorbic} />
            <MetricRow label="Sugar %" value={summary.sugar} color={PARAM_COLORS.sugar} />
          </div>
        </div>
      </div>

      <div className="admin-report-charts-row">
        <div className="admin-report-panel admin-report-chart-panel">
          <h3 className="admin-report-panel-title">Parameters (pH, citric, ascorbic, sugar)</h3>
          <div className="admin-chart-container" style={{ overflow: "visible" }}>
            {paramsPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart margin={{ top: 8, right: 8, left: 8, bottom: 48 }}>
                  <Pie
                    data={paramsPieData}
                    cx="50%"
                    cy="42%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={2}
                    dataKey="value"
                    label={false}
                  />
                  <Tooltip
                    contentStyle={{ background: "#1e293b", border: "1px solid #475569" }}
                    formatter={(_v: number, _name: string, item: { payload?: { raw?: number; name?: string } }) => {
                      const raw = item.payload?.raw;
                      const label = item.payload?.name ?? "";
                      if (raw == null) return ["—", label];
                      const display = label === "pH" ? raw.toFixed(2) : raw < 0.01 ? raw.toFixed(4) : raw.toFixed(2);
                      return [display, label];
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    layout="horizontal"
                    wrapperStyle={{ color: "#fff", paddingTop: "8px" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#94a3b8" }}>
                No data — values will appear when readings are available
              </div>
            )}
          </div>
        </div>
        <div className="admin-report-panel admin-report-chart-panel admin-robot-stage-panel">
          <h3 className="admin-report-panel-title">Robot Position</h3>
          <div className="admin-robot-stage-list" role="status" aria-live="polite">
            {robotStages.map(({ stage, label }) => {
              const active = robotStage === stage;
              const isDetection = stage === "detection_station";
              return (
                <div
                  key={stage}
                  className={`admin-robot-stage-item ${active ? "admin-robot-stage-item-active" : ""}`}
                >
                  <span
                    className={[
                      "admin-robot-stage-light",
                      active ? "admin-robot-stage-light-active" : "",
                      active && isDetection ? "admin-robot-stage-light-blink" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    aria-hidden
                  />
                  <span>{label}</span>
                </div>
              );
            })}
          </div>
          {!robotStage && <p className="admin-robot-stage-waiting">Waiting for robot status…</p>}
        </div>
        <div className="admin-report-panel admin-report-chart-panel">
          <h3 className="admin-report-panel-title">Cleaning verification</h3>
          <div className="admin-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cleaningChartData} margin={{ top: 8, right: 12, left: 8, bottom: 32 }} barCategoryGap="20%">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.12)" vertical={false} />
                <XAxis dataKey="name" stroke="#fff" tick={{ fill: "#fff", fontSize: 11 }} interval={0} />
                <YAxis stroke="#fff" tick={{ fill: "#fff" }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #475569" }}
                  labelFormatter={() => cleaningChartVerdict}
                  formatter={(
                    v: number,
                    name: string,
                    item: {
                      payload?: {
                        initialRaw?: number;
                        rangeLabel?: string;
                        currentRaw?: number | null;
                        hasReading?: boolean;
                        matches?: boolean;
                      };
                    }
                  ) => {
                    const p = item.payload;
                    if (name === "Permanent reading") {
                      const range = p?.rangeLabel;
                      if (range) return [range, name];
                      const raw = p?.initialRaw;
                      return [raw != null ? raw.toFixed(2) : String(v), name];
                    }
                    if (!p?.hasReading) return ["No reading", "Current reading"];
                    const raw = p?.currentRaw;
                    const display = raw != null ? raw.toFixed(2) : String(v);
                    const suffix = p?.matches ? " (match)" : " (mismatch)";
                    return [`${display}${suffix}`, name];
                  }}
                />
                <Legend verticalAlign="bottom" layout="horizontal" wrapperStyle={{ color: "#fff", paddingTop: "12px" }} />
                <Bar
                  dataKey="initial"
                  name="Permanent reading"
                  fill={cleaningChartColors.permanent}
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="current"
                  name="Current reading"
                  fill={cleaningChartColors.current}
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

    </div>
  );
}

export default function AdminDashboard() {
  const VALIDATION_DEMO_DATE = "2026-06-30";
  const today = format(new Date(), "yyyy-MM-dd");
  const [dateFrom, setDateFrom] = useState(today);
  const [dateTo, setDateTo] = useState(today);
  const [periodType, setPeriodType] = useState<"day" | "week" | "month">("day");
  const [selectedDate, setSelectedDate] = useState(today);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedWeek, setSelectedWeek] = useState(getISOWeek(new Date()));
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [statusFilter] = useState<string>("");
  const [readings, setReadings] = useState<SensorReadingItem[]>([]);
  const [liveReadings, setLiveReadings] = useState<LiveReadingsState>([null, null, null]);
  const [liveSnapshot, setLiveSnapshot] = useState<SensorSnapshot | null>(null);
  const [robotStage, setRobotStage] = useState<RobotStage | null>(null);
  const [cleaningReading, setCleaningReading] = useState<CleaningSensorState | null>(null);
  const [completedVerdict, setCompletedVerdict] = useState<"authentic" | "adulterated" | null>(null);
  const [esp32Buffer, setEsp32Buffer] = useState({ count: 0, required: 3 });
  const lastBatchMaxPredId = useRef(0);
  const prevBufferedCount = useRef(0);
  const liveFilledCount = liveReadings.filter((r) => r != null).length;
  const isCollectingBatch = esp32Buffer.count > 0 && esp32Buffer.count < esp32Buffer.required;
  const sessionComplete = !isCollectingBatch && liveFilledCount >= esp32Buffer.required;

  const [predictions, setPredictions] = useState<PredictionItem[]>([]);
  const [logs, setLogs] = useState<SystemLogItem[]>([]);
  const [loadingReadings, setLoadingReadings] = useState(false);
  const [loadingPredictions, setLoadingPredictions] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logLevelFilter, setLogLevelFilter] = useState("");
  const [logComponentFilter, setLogComponentFilter] = useState("");
  const [logSearchFilter, setLogSearchFilter] = useState("");

  const loadReadings = useCallback(async () => {
    setLoadingReadings(true);
    setError(null);
    try {
      const data = await fetchReadings({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        limit: EXPORT_FETCH_LIMIT,
      });
      setReadings(data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingReadings(false);
    }
  }, [dateFrom, dateTo]);

  const loadPredictions = useCallback(async () => {
    setLoadingPredictions(true);
    setError(null);
    try {
      const data = await fetchPredictions({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        status: statusFilter || undefined,
        limit: EXPORT_FETCH_LIMIT,
      });
      setPredictions(data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingPredictions(false);
    }
  }, [dateFrom, dateTo, statusFilter]);

  const loadLogs = useCallback(async () => {
    setLoadingLogs(true);
    setError(null);
    try {
      const data = await fetchLogs({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        level: logLevelFilter || undefined,
        component: logComponentFilter || undefined,
        search: logSearchFilter || undefined,
        limit: EXPORT_FETCH_LIMIT,
      });
      setLogs(data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingLogs(false);
    }
  }, [dateFrom, dateTo, logLevelFilter, logComponentFilter, logSearchFilter]);

  const loadAll = useCallback(() => {
    loadReadings();
    loadPredictions();
    loadLogs();
  }, [loadReadings, loadPredictions, loadLogs]);

  const handleApplyPeriod = useCallback(() => {
    let nextFrom = dateFrom;
    let nextTo = dateTo;
    if (periodType === "day") {
      nextFrom = selectedDate;
      nextTo = selectedDate;
    } else if (periodType === "week") {
      const jan4 = new Date(selectedYear, 0, 4);
      const mondayOfWeek1 = startOfWeek(jan4, { weekStartsOn: 1 });
      const targetMonday = addWeeks(mondayOfWeek1, selectedWeek - 1);
      nextFrom = format(targetMonday, "yyyy-MM-dd");
      nextTo = format(endOfWeek(targetMonday, { weekStartsOn: 1 }), "yyyy-MM-dd");
    } else {
      nextFrom = format(startOfMonth(new Date(selectedYear, selectedMonth - 1)), "yyyy-MM-dd");
      nextTo = format(endOfMonth(new Date(selectedYear, selectedMonth - 1)), "yyyy-MM-dd");
    }
    if (nextFrom === dateFrom && nextTo === dateTo) {
      loadAll();
    } else {
      setDateFrom(nextFrom);
      setDateTo(nextTo);
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth, dateFrom, dateTo, loadAll]);

  const handleGraphDateChange = useCallback((date: string) => {
    if (!date) return;
    setSelectedDate(date);
    setPeriodType("day");
    setDateFrom(date);
    setDateTo(date);
  }, []);

  const location = useLocation();
  const panelIndex = useMemo(() => {
    const p = location.pathname;
    if (p === "/admin/readings") return 0;
    if (p === "/admin/predictions") return 1;
    if (p === "/admin/logs") return 2;
    if (p === "/admin/graphs") return 3;
    return -1; // Overview
  }, [location.pathname]);

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateFrom, dateTo]);

  useEffect(() => {
    if (panelIndex < 0 || panelIndex > 2) return;
    loadAll();
    const timer = setInterval(loadAll, 4000);
    return () => clearInterval(timer);
  }, [panelIndex, loadAll]);

  /** Poll ESP32 live sensor values + latest ML batch for overview panels. */
  useEffect(() => {
    let cancelled = false;

    const pollEsp32Live = async () => {
      try {
        const live = await fetchEsp32Live();
        if (cancelled) return;

        const required = live.required_count || 3;
        const collecting = live.buffered_count > 0 && live.buffered_count < required;
        const justCompleted =
          prevBufferedCount.current > 0 && live.buffered_count === 0;
        const recentSaved =
          !!live.latest_saved?.timestamp &&
          Date.now() - Date.parse(live.latest_saved.timestamp) <= 120_000;

        const rs = live.robot_status;
        let stage: RobotStage | null = rs?.stage ?? null;
        if (rs?.updated_at) {
          const ageMs = Date.now() - Date.parse(rs.updated_at);
          // Match backend ROBOT_STATUS_STALE_SECONDS (180s).
          if (!Number.isFinite(ageMs) || ageMs > 180_000) {
            stage = null;
          }
        } else if (!rs) {
          stage = null;
        }
        setRobotStage(stage);
        setEsp32Buffer({ count: live.buffered_count, required });
        const cl = live.latest_cleaning;
        if (cl && cl.tds != null && cl.temperature != null && cl.turbidity != null) {
          setCleaningReading({
            ph: cl.pH,
            tds: cl.tds,
            turbidity: cl.turbidity,
            temperature: cl.temperature,
          });
        }

        // Finished batch from public esp32-live (no auth) — readings, graph, authenticity.
        if (live.completed_batch?.readings?.length) {
          const slots = buildCompletedBatchSlots(live.completed_batch);
          setLiveReadings(slots);
          const summary = completedBatchToSummary(live.completed_batch);
          const status = live.completed_batch.average?.authenticity_status;
          setCompletedVerdict(
            status === "authentic" ? "authentic" : status === "adulterated" ? "adulterated" : null,
          );
          if (live.current) {
            setLiveSnapshot({
              pH: PH_SENSOR_ENABLED ? live.current.pH : null,
              tds: live.current.tds,
              temperature: live.current.temperature,
              turbidity: live.current.turbidity,
            });
          }
          prevBufferedCount.current = live.buffered_count;
          return;
        }

        // Keep the live sensor strip if the ESP32 already posted a current snapshot.
        if (live.current) {
          setLiveSnapshot({
            pH: PH_SENSOR_ENABLED ? live.current.pH : null,
            tds: live.current.tds,
            temperature: live.current.temperature,
            turbidity: live.current.turbidity,
          });
        }

        // Idle / cleared buffer: wipe columns unless a batch just finished or was saved recently.
        if (live.buffered_count === 0 && !justCompleted && !recentSaved) {
          if (!live.current) {
            setLiveReadings([null, null, null]);
            setLiveSnapshot(null);
          }
          setCompletedVerdict(null);
          prevBufferedCount.current = 0;
          if (!live.current) return;
        }

        prevBufferedCount.current = live.buffered_count;

        // Sensor strip during active session or for a batch saved in the last 2 minutes.
        if (live.current && (live.buffered_count > 0 || justCompleted || recentSaved)) {
          setLiveSnapshot({
            pH: PH_SENSOR_ENABLED ? live.current.pH : null,
            tds: live.current.tds,
            temperature: live.current.temperature,
            turbidity: live.current.turbidity,
          });
        } else if (live.buffered_count === 0 && !live.current) {
          setLiveSnapshot(null);
        }

        // 1/3 → First column, 2/3 → Second column
        if (collecting || live.buffered_count > 0) {
          setLiveReadings(buildBatchSlots(live));
          if (collecting) return;
        }

        // Load completed ML batch after 3rd upload or when reopening dashboard with a fresh save.
        if (!justCompleted && !recentSaved) return;

        const [preds, sensorRows] = await Promise.all([
          fetchPredictions({ limit: required }),
          fetchReadings({ limit: required }),
        ]);
        if (cancelled || preds.length < required) {
          setLiveReadings([null, null, null]);
          setLiveSnapshot(null);
          return;
        }

        // Ignore stale DB batches (e.g. after clearing a test buffer).
        const ageMs = Date.now() - new Date(preds[0].timestamp).getTime();
        if (Number.isFinite(ageMs) && ageMs > 120_000) {
          setLiveReadings([null, null, null]);
          setLiveSnapshot(null);
          return;
        }

        const batchTs = preds[0].timestamp.slice(0, 19);
        const batch = preds.filter((p) => p.timestamp.slice(0, 19) === batchTs);
        if (batch.length < required) return;

        const maxId = Math.max(...batch.map((p) => p.id));
        if (maxId <= lastBatchMaxPredId.current) return;
        lastBatchMaxPredId.current = maxId;

        const readingMap = new Map(sensorRows.map((r) => [r.id, r]));
        const ordered = [...batch].reverse();
        const slots: LiveReadingsState = [
          readingMap.has(ordered[0].reading)
            ? predictionToLiveSlot(ordered[0], readingMap.get(ordered[0].reading)!)
            : null,
          ordered[1] && readingMap.has(ordered[1].reading)
            ? predictionToLiveSlot(ordered[1], readingMap.get(ordered[1].reading)!)
            : null,
          ordered[2] && readingMap.has(ordered[2].reading)
            ? predictionToLiveSlot(ordered[2], readingMap.get(ordered[2].reading)!)
            : null,
        ];
        setLiveReadings(slots);
        setPredictions((prev) => {
          const merged = [...preds, ...prev.filter((p) => !preds.some((x) => x.id === p.id))];
          return merged.slice(0, 100);
        });
        setReadings((prev) => {
          const merged = [...sensorRows, ...prev.filter((r) => !sensorRows.some((x) => x.id === r.id))];
          return merged.slice(0, 100);
        });
      } catch {
        /* live poll is best-effort */
      }
    };

    pollEsp32Live();
    const timer = setInterval(pollEsp32Live, 2500);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const handleDownloadPDF = useCallback(async () => {
    try {
      let agg: Awaited<ReturnType<typeof fetchDaily>>;
      let filename: string;
      if (periodType === "day") {
        agg = await fetchDaily(selectedDate);
        filename = `sensor-readings-${selectedDate}.pdf`;
      } else if (periodType === "week") {
        agg = await fetchWeekly(selectedYear, selectedWeek);
        filename = `sensor-readings-${selectedYear}-W${selectedWeek}.pdf`;
      } else {
        agg = await fetchMonthly(selectedYear, selectedMonth);
        filename = `sensor-readings-${selectedYear}-${String(selectedMonth).padStart(2, "0")}.pdf`;
      }

      const pdf = new jsPDF("portrait", "mm", "a4");
      const pageW = pdf.internal.pageSize.getWidth();
      let y = 15;

      pdf.setFontSize(16);
      const title = "Coconut Water Quality Report";
      const titleX = (pageW - pdf.getTextWidth(title)) / 2;
      pdf.text(title, titleX, y);
      y += 10;

      pdf.setFontSize(10);
      pdf.text(`Period: ${agg.period}`, 14, y);
      y += 6;
      pdf.text(`Readings: ${agg.count} | Authentic: ${agg.authenticity.authentic} | Adulterated: ${agg.authenticity.adulterated} | Status: ${agg.status}`, 14, y);
      y += 10;

      pdf.text("Averages:", 14, y);
      y += 6;
      pdf.text(`pH: ${agg.averages.ph ?? "—"} | TDS: ${agg.averages.tds ?? "—"} | Temp: ${agg.averages.temperature ?? "—"} | Turbidity: ${agg.averages.turbidity ?? "—"}`, 14, y);
      y += 6;
      pdf.text(`Sugar %: ${agg.averages.predicted_sugar ?? "—"} | Citric %: ${agg.averages.predicted_citric ?? "—"} | Ascorbic %: ${agg.averages.predicted_ascorbic ?? "—"}`, 14, y);
      y += 12;

      if (readings.length > 0) {
        const { dateFrom: exportFrom, dateTo: exportTo } = resolvePeriodRange(
          periodType,
          selectedDate,
          selectedYear,
          selectedWeek,
          selectedMonth,
        );
        const exportReadings = await fetchReadings({
          date_from: exportFrom,
          date_to: exportTo,
          limit: EXPORT_FETCH_LIMIT,
        });

        pdf.text(`Sensor readings (${exportReadings.length}):`, 14, y);
        y += 6;
        const colW = (pageW - 28) / 7;
        const headers = ["ID", "Date", "Time", "pH", "TDS", "Temp", "Turb"];
        pdf.setFont("helvetica", "bold");
        headers.forEach((h, i) => pdf.text(h, 14 + i * colW, y));
        pdf.setFont("helvetica", "normal");
        y += 6;
        for (const r of exportReadings) {
          if (y > 270) {
            pdf.addPage();
            y = 15;
          }
          const dt = new Date(r.timestamp);
          const dateStr = format(dt, "yyyy-MM-dd");
          const timeStr = format(dt, "HH:mm");
          const row = [String(r.id), dateStr, timeStr, String(r.ph), String(r.tds), String(r.temperature), String(r.turbidity)];
          row.forEach((v, i) => pdf.text(v.substring(0, 12), 14 + i * colW, y));
          y += 5;
        }
      }

      pdf.save(filename);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth, readings]);

  const fetchPeriodAggregation = useCallback(async (): Promise<AggregationResponse> => {
    if (periodType === "day") return fetchDaily(selectedDate);
    if (periodType === "week") return fetchWeekly(selectedYear, selectedWeek);
    return fetchMonthly(selectedYear, selectedMonth);
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth]);

  const handleDownloadReadingsCsv = useCallback(async () => {
    try {
      const fileBase = getPeriodFileBase("sensor-readings", periodType, selectedDate, selectedYear, selectedWeek, selectedMonth);
      const { dateFrom: exportFrom, dateTo: exportTo } = resolvePeriodRange(
        periodType, selectedDate, selectedYear, selectedWeek, selectedMonth,
      );
      const [agg, exportReadings] = await Promise.all([
        fetchPeriodAggregation(),
        fetchReadings({ date_from: exportFrom, date_to: exportTo, limit: EXPORT_FETCH_LIMIT }),
      ]);
      const summary = buildAggregationSummaryRows(agg, agg.period);
      const dataRows = sensorReadingExportRows(exportReadings);
      downloadCsvFile(`${fileBase}.csv`, [...summary, [], ["Sensor readings"], ...dataRows]);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth, fetchPeriodAggregation]);

  const handleDownloadReadingsExcel = useCallback(async () => {
    try {
      const fileBase = getPeriodFileBase("sensor-readings", periodType, selectedDate, selectedYear, selectedWeek, selectedMonth);
      const { dateFrom: exportFrom, dateTo: exportTo } = resolvePeriodRange(
        periodType, selectedDate, selectedYear, selectedWeek, selectedMonth,
      );
      const [agg, exportReadings] = await Promise.all([
        fetchPeriodAggregation(),
        fetchReadings({ date_from: exportFrom, date_to: exportTo, limit: EXPORT_FETCH_LIMIT }),
      ]);
      const summary = buildAggregationSummaryRows(agg, agg.period);
      const dataRows = sensorReadingExportRows(exportReadings);
      downloadExcelFile(`${fileBase}.xlsx`, [
        { name: "Summary", rows: summary },
        { name: "Sensor readings", rows: dataRows },
      ]);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth, fetchPeriodAggregation]);

  const handleDownloadPredictionsCsv = useCallback(async () => {
    try {
      const fileBase = getPeriodFileBase("predictions", periodType, selectedDate, selectedYear, selectedWeek, selectedMonth);
      const { dateFrom: exportFrom, dateTo: exportTo } = resolvePeriodRange(
        periodType, selectedDate, selectedYear, selectedWeek, selectedMonth,
      );
      const [agg, exportPredictions, exportReadings] = await Promise.all([
        fetchPeriodAggregation(),
        fetchPredictions({ date_from: exportFrom, date_to: exportTo, limit: EXPORT_FETCH_LIMIT }),
        fetchReadings({ date_from: exportFrom, date_to: exportTo, limit: EXPORT_FETCH_LIMIT }),
      ]);
      const readingById = new Map(exportReadings.map((r) => [r.id, r]));
      const summary = buildAggregationSummaryRows(agg, agg.period);
      const dataRows = predictionExportRows(exportPredictions, readingById);
      downloadCsvFile(`${fileBase}.csv`, [...summary, [], ["Predictions"], ...dataRows]);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth, fetchPeriodAggregation]);

  const handleDownloadPredictionsExcel = useCallback(async () => {
    try {
      const fileBase = getPeriodFileBase("predictions", periodType, selectedDate, selectedYear, selectedWeek, selectedMonth);
      const { dateFrom: exportFrom, dateTo: exportTo } = resolvePeriodRange(
        periodType, selectedDate, selectedYear, selectedWeek, selectedMonth,
      );
      const [agg, exportPredictions, exportReadings] = await Promise.all([
        fetchPeriodAggregation(),
        fetchPredictions({ date_from: exportFrom, date_to: exportTo, limit: EXPORT_FETCH_LIMIT }),
        fetchReadings({ date_from: exportFrom, date_to: exportTo, limit: EXPORT_FETCH_LIMIT }),
      ]);
      const readingById = new Map(exportReadings.map((r) => [r.id, r]));
      const summary = buildAggregationSummaryRows(agg, agg.period);
      const dataRows = predictionExportRows(exportPredictions, readingById);
      downloadExcelFile(`${fileBase}.xlsx`, [
        { name: "Summary", rows: summary },
        { name: "Predictions", rows: dataRows },
      ]);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth, fetchPeriodAggregation]);

  const buildDefectRows = useCallback(async () => {
    const { dateFrom: exportFrom, dateTo: exportTo } = resolvePeriodRange(
      periodType, selectedDate, selectedYear, selectedWeek, selectedMonth,
    );
    const [exportPredictions, exportReadings] = await Promise.all([
      fetchPredictions({ date_from: exportFrom, date_to: exportTo, limit: EXPORT_FETCH_LIMIT }),
      fetchReadings({ date_from: exportFrom, date_to: exportTo, limit: EXPORT_FETCH_LIMIT }),
    ]);
    const readingById = new Map(exportReadings.map((r) => [r.id, r]));
    const headers = ["ID", "Date", "Time", "pH", "Sugar %", "Citric %", "Ascorbic %", "Issue"];
    const rows: string[][] = [headers];
    for (const p of exportPredictions.filter((x) => x.authenticity_status === "adulterated")) {
      const r = readingById.get(p.reading);
      const ph = r?.ph ?? 0;
      const sugar = p.predicted_sugar;
      const citric = p.predicted_citric;
      const ascorbic = p.predicted_ascorbic;
      const issues: string[] = [];
      if (ph < TYPICAL_RANGES.ph.min) issues.push(`pH low (${ph.toFixed(2)})`);
      else if (ph > TYPICAL_RANGES.ph.max) issues.push(`pH high (${ph.toFixed(2)})`);
      if (sugar < TYPICAL_RANGES.sugar.min) issues.push(`Sugar low (${sugar.toFixed(2)}%)`);
      else if (sugar > TYPICAL_RANGES.sugar.max) issues.push(`Sugar high (${sugar.toFixed(2)}%)`);
      if (citric < TYPICAL_RANGES.citric.min) issues.push(`Citric low (${citric.toFixed(4)}%)`);
      else if (citric > TYPICAL_RANGES.citric.max) issues.push(`Citric high (${citric.toFixed(4)}%)`);
      if (ascorbic < TYPICAL_RANGES.ascorbic.min) issues.push(`Ascorbic low (${ascorbic.toFixed(4)}%)`);
      else if (ascorbic > TYPICAL_RANGES.ascorbic.max) issues.push(`Ascorbic high (${ascorbic.toFixed(4)}%)`);
      const dt = new Date(p.timestamp);
      rows.push([
        String(p.id),
        format(dt, "yyyy-MM-dd"),
        format(dt, "HH:mm"),
        r?.ph != null ? String(r.ph) : "",
        String(sugar),
        String(citric),
        String(ascorbic),
        issues.length > 0 ? issues.join("; ") : "Out of range",
      ]);
    }
    return rows;
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth]);

  const handleDownloadDefectsCsv = useCallback(async () => {
    try {
      const fileBase = getPeriodFileBase("defects", periodType, selectedDate, selectedYear, selectedWeek, selectedMonth);
      const dataRows = await buildDefectRows();
      downloadCsvFile(`${fileBase}.csv`, [
        ["Coconut Water Quality Report — Defects"],
        ["Period", periodType === "day" ? selectedDate : periodType === "week" ? `${selectedYear} W${selectedWeek}` : `${selectedYear}-${String(selectedMonth).padStart(2, "0")}`],
        [],
        ...dataRows,
      ]);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth, buildDefectRows]);

  const handleDownloadDefectsExcel = useCallback(async () => {
    try {
      const fileBase = getPeriodFileBase("defects", periodType, selectedDate, selectedYear, selectedWeek, selectedMonth);
      const dataRows = await buildDefectRows();
      downloadExcelFile(`${fileBase}.xlsx`, [{ name: "Defects", rows: dataRows }]);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth, buildDefectRows]);

  const handleDownloadPredictionsPDF = useCallback(async () => {
    try {
      let filename: string;
      if (periodType === "day") {
        filename = `predictions-${selectedDate}.pdf`;
      } else if (periodType === "week") {
        filename = `predictions-${selectedYear}-W${selectedWeek}.pdf`;
      } else {
        filename = `predictions-${selectedYear}-${String(selectedMonth).padStart(2, "0")}.pdf`;
      }

      const { dateFrom: exportFrom, dateTo: exportTo } = resolvePeriodRange(
        periodType,
        selectedDate,
        selectedYear,
        selectedWeek,
        selectedMonth,
      );
      const [exportPredictions, exportReadings] = await Promise.all([
        fetchPredictions({ date_from: exportFrom, date_to: exportTo, limit: EXPORT_FETCH_LIMIT }),
        fetchReadings({ date_from: exportFrom, date_to: exportTo, limit: EXPORT_FETCH_LIMIT }),
      ]);

      const pdf = new jsPDF("portrait", "mm", "a4");
      const pageW = pdf.internal.pageSize.getWidth();
      let y = 15;

      pdf.setFontSize(16);
      const title = "Coconut Water Quality Report";
      const titleX = (pageW - pdf.getTextWidth(title)) / 2;
      pdf.text(title, titleX, y);
      y += 10;

      pdf.setFontSize(10);
      pdf.text(`Period: ${periodType} — ${periodType === "day" ? selectedDate : periodType === "week" ? `${selectedYear} W${selectedWeek}` : `${selectedYear}-${String(selectedMonth).padStart(2, "0")}`}`, 14, y);
      y += 6;
      pdf.text(`Total readings exported: ${exportPredictions.length}`, 14, y);
      y += 10;

      if (exportPredictions.length > 0) {
        const readingById = new Map(exportReadings.map((r) => [r.id, r]));
        const colW = (pageW - 28) / 10;
        const headers = ["ID", "Reading", "Date", "Time", "pH", "Sugar %", "Citric %", "Ascorbic %", "Status", "Conf"];
        pdf.setFont("helvetica", "bold");
        headers.forEach((h, i) => pdf.text(h, 14 + i * colW, y));
        pdf.setFont("helvetica", "normal");
        y += 6;
        for (const p of exportPredictions) {
          if (y > 270) {
            pdf.addPage();
            y = 15;
          }
          const r = readingById.get(p.reading);
          const status = p.authenticity_status === "authentic" ? "Authentic" : "Adulterated";
          const dt = new Date(p.timestamp);
          const dateStr = format(dt, "yyyy-MM-dd");
          const timeStr = format(dt, "HH:mm");
          const row = [
            String(p.id),
            String(p.reading),
            dateStr,
            timeStr,
            r?.ph != null ? String(r.ph) : "—",
            String(p.predicted_sugar),
            String(p.predicted_citric),
            String(p.predicted_ascorbic),
            status,
            confidencePercent(p.confidence),
          ];
          row.forEach((v, i) => pdf.text(v.substring(0, 8), 14 + i * colW, y));
          y += 5;
        }
      } else {
        pdf.text("No predictions for this period.", 14, y);
      }

      pdf.save(filename);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth]);

  const handleDownloadDefectsPDF = useCallback(async () => {
    try {
      const defects = predictions
        .filter((p) => p.authenticity_status === "adulterated")
        .map((p) => {
          const r = readings.find((x) => x.id === p.reading);
          const ph = r?.ph ?? 0;
          const sugar = p.predicted_sugar;
          const citric = p.predicted_citric;
          const ascorbic = p.predicted_ascorbic;
          const issues: string[] = [];
          if (ph < TYPICAL_RANGES.ph.min) issues.push(`pH low (${ph.toFixed(2)})`);
          else if (ph > TYPICAL_RANGES.ph.max) issues.push(`pH high (${ph.toFixed(2)})`);
          if (sugar < TYPICAL_RANGES.sugar.min) issues.push(`Sugar low (${sugar.toFixed(2)}%)`);
          else if (sugar > TYPICAL_RANGES.sugar.max) issues.push(`Sugar high (${sugar.toFixed(2)}%)`);
          if (citric < TYPICAL_RANGES.citric.min) issues.push(`Citric low (${citric.toFixed(4)}%)`);
          else if (citric > TYPICAL_RANGES.citric.max) issues.push(`Citric high (${citric.toFixed(4)}%)`);
          if (ascorbic < TYPICAL_RANGES.ascorbic.min) issues.push(`Ascorbic low (${ascorbic.toFixed(4)}%)`);
          else if (ascorbic > TYPICAL_RANGES.ascorbic.max) issues.push(`Ascorbic high (${ascorbic.toFixed(4)}%)`);
          return {
            id: p.id,
            date: format(new Date(p.timestamp), "yyyy-MM-dd"),
            time: format(new Date(p.timestamp), "HH:mm"),
            ph: r?.ph ?? "—",
            sugar,
            citric,
            ascorbic,
            issue: issues.length > 0 ? issues.join("; ") : "Out of range",
          };
        });

      let filename: string;
      if (periodType === "day") {
        filename = `defects-${selectedDate}.pdf`;
      } else if (periodType === "week") {
        filename = `defects-${selectedYear}-W${selectedWeek}.pdf`;
      } else {
        filename = `defects-${selectedYear}-${String(selectedMonth).padStart(2, "0")}.pdf`;
      }

      const pdf = new jsPDF("portrait", "mm", "a4");
      const pageW = pdf.internal.pageSize.getWidth();
      let y = 15;

      pdf.setFontSize(16);
      const title = "Coconut Water Quality Report — Defects";
      const titleX = (pageW - pdf.getTextWidth(title)) / 2;
      pdf.text(title, titleX, y);
      y += 10;

      pdf.setFontSize(10);
      pdf.text(`Period: ${periodType === "day" ? selectedDate : periodType === "week" ? `${selectedYear} W${selectedWeek}` : `${selectedYear}-${String(selectedMonth).padStart(2, "0")}`} | Low-quality count: ${defects.length}`, 14, y);
      y += 10;

      if (defects.length > 0) {
        const colW = (pageW - 28) / 8;
        const headers = ["ID", "Date", "Time", "pH", "Sugar %", "Citric %", "Ascorbic %", "Issue"];
        pdf.setFont("helvetica", "bold");
        headers.forEach((h, i) => pdf.text(h, 14 + i * colW, y));
        pdf.setFont("helvetica", "normal");
        y += 6;
        for (const d of defects) {
          if (y > 270) {
            pdf.addPage();
            y = 15;
          }
          const row = [
            String(d.id),
            d.date,
            d.time,
            String(d.ph),
            String(d.sugar),
            String(d.citric),
            String(d.ascorbic),
            d.issue.substring(0, 30),
          ];
          row.forEach((v, i) => pdf.text(v.substring(0, 10), 14 + i * colW, y));
          y += 5;
        }
      } else {
        pdf.text("No low-quality defects in this period.", 14, y);
      }

      pdf.save(filename);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth, predictions, readings]);

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const formatTs = (ts: string) => {
    try {
      return format(new Date(ts), "yyyy-MM-dd HH:mm");
    } catch {
      return ts;
    }
  };

  /** Join sensor readings with ML predictions for correlation / trend graphs. */
  const joinedGraphRows = useMemo(() => {
    const readingById = new Map(readings.map((r) => [r.id, r]));
    return [...predictions]
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .map((p) => {
        const r = readingById.get(p.reading);
        if (!r) return null;
        return {
          time: format(new Date(p.timestamp), "HH:mm:ss"),
          date: format(new Date(p.timestamp), "yyyy-MM-dd"),
          pH: r.ph,
          TDS: r.tds,
          Temperature: r.temperature,
          Turbidity: r.turbidity,
          Sugar: p.predicted_sugar,
          Citric: p.predicted_citric,
          Ascorbic: p.predicted_ascorbic,
          status: p.authenticity_status,
        };
      })
      .filter((row): row is NonNullable<typeof row> => row != null);
  }, [readings, predictions]);

  const sensorGraphData = useMemo(
    () =>
      [...readings]
        .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
        .slice(-100)
        .map((r) => ({
          time: format(new Date(r.timestamp), "HH:mm:ss"),
          pH: r.ph,
          TDS: r.tds,
          Temperature: r.temperature,
          Turbidity: r.turbidity,
        })),
    [readings],
  );

  const predictionGraphData = useMemo(
    () =>
      joinedGraphRows.slice(-100).map((row) => ({
        time: row.time,
        Sugar: row.Sugar,
        Citric: row.Citric,
        Ascorbic: row.Ascorbic,
      })),
    [joinedGraphRows],
  );

  const authenticityGraphData = useMemo(
    () => [
      {
        name: "Samples",
        Authentic: predictions.filter((p) => p.authenticity_status === "authentic").length,
        Adulterated: predictions.filter((p) => p.authenticity_status === "adulterated").length,
      },
    ],
    [predictions],
  );

  const pearsonR = (xs: number[], ys: number[]): number | null => {
    const n = Math.min(xs.length, ys.length);
    if (n < 2) return null;
    const x = xs.slice(0, n);
    const y = ys.slice(0, n);
    const meanX = x.reduce((s, v) => s + v, 0) / n;
    const meanY = y.reduce((s, v) => s + v, 0) / n;
    let num = 0;
    let denX = 0;
    let denY = 0;
    for (let i = 0; i < n; i++) {
      const dx = x[i] - meanX;
      const dy = y[i] - meanY;
      num += dx * dy;
      denX += dx * dx;
      denY += dy * dy;
    }
    const den = Math.sqrt(denX * denY);
    if (den === 0) return null;
    return num / den;
  };

  const correlationCharts = useMemo(() => {
    const rows = joinedGraphRows;
    const make = (
      title: string,
      xKey: "TDS" | "pH" | "Temperature" | "Turbidity",
      yKey: "Sugar" | "Citric" | "Ascorbic",
      xLabel: string,
      yLabel: string,
      color: string,
    ) => {
      const data = rows.map((r) => ({
        x: r[xKey],
        y: r[yKey],
        status: r.status,
      }));
      const r = pearsonR(
        data.map((d) => d.x),
        data.map((d) => d.y),
      );
      return { title, xLabel, yLabel, color, data, r };
    };
    return [
      make("Sugar % vs TDS", "TDS", "Sugar", "TDS (ppm)", "Sugar %", "#27AE60"),
      make("Citric acid % vs pH", "pH", "Citric", "pH", "Citric acid %", "#F5A623"),
      make("Ascorbic acid % vs pH", "pH", "Ascorbic", "pH", "Ascorbic acid %", "#14B8A6"),
      make("Sugar % vs pH", "pH", "Sugar", "pH", "Sugar %", "#4A90E2"),
      make("Citric acid % vs TDS", "TDS", "Citric", "TDS (ppm)", "Citric acid %", "#E67E22"),
      make("Ascorbic acid % vs TDS", "TDS", "Ascorbic", "TDS (ppm)", "Ascorbic acid %", "#8B5CF6"),
    ];
  }, [joinedGraphRows]);

  const isOverview = panelIndex === -1;

  return (
    <div className="admin-dashboard-panels admin-dashboard-full">
      {error && (
        <div className="admin-error-banner" role="alert">
          <p style={{ margin: 0 }}>{error}</p>
          <button type="button" onClick={() => setError(null)} aria-label="Dismiss">×</button>
        </div>
      )}
      {isOverview && (
        <div className="admin-report-overview-wrap">
          <SensorPredictPanel
            currentSnapshot={liveSnapshot}
            bufferedCount={esp32Buffer.count}
            requiredCount={esp32Buffer.required}
            waiting={!liveSnapshot}
          />
          <ProductionReportOverview
            liveReadings={liveReadings}
            cleaningReading={cleaningReading}
            activeReadingIndex={sessionComplete ? 0 : esp32Buffer.count + 1}
            bufferedCount={esp32Buffer.count}
            requiredCount={esp32Buffer.required}
            robotStage={robotStage}
            completedVerdict={completedVerdict}
          />
        </div>
      )}

      <section
        className={`dashboard-card admin-panel-pane admin-readings-panel ${panelIndex === 0 ? "active" : ""}`}
        style={{ marginBottom: "1.5rem", overflowX: "auto", display: panelIndex === 0 ? "block" : "none" }}
        aria-hidden={panelIndex !== 0}
      >
        <h2 className="dashboard-section-title">Sensor readings</h2>
        <PeriodSelectorBar
          periodType={periodType}
          setPeriodType={setPeriodType}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          selectedYear={selectedYear}
          setSelectedYear={setSelectedYear}
          selectedWeek={selectedWeek}
          setSelectedWeek={setSelectedWeek}
          selectedMonth={selectedMonth}
          setSelectedMonth={setSelectedMonth}
          onApply={handleApplyPeriod}
          onDownloadPdf={handleDownloadPDF}
          onDownloadCsv={handleDownloadReadingsCsv}
          onDownloadExcel={handleDownloadReadingsExcel}
          loading={loadingReadings || loadingPredictions || loadingLogs}
          variant="light"
        />
        {loadingReadings ? (
          <p className="admin-readings-loading">Loading…</p>
        ) : (
          <div className="admin-readings-table-wrap">
            <table className="admin-readings-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>pH</th>
                  <th>TDS</th>
                  <th>Temp</th>
                  <th>Turbidity</th>
                </tr>
              </thead>
              <tbody>
                {readings.length === 0 ? (
                  <tr><td colSpan={7}>No readings.</td></tr>
                ) : (
                  readings.map((r) => {
                    const d = (() => {
                      try {
                        const dt = new Date(r.timestamp);
                        return { date: format(dt, "yyyy-MM-dd"), time: format(dt, "HH:mm") };
                      } catch {
                        return { date: "—", time: "—" };
                      }
                    })();
                    return (
                      <tr key={r.id}>
                        <td>{r.id}</td>
                        <td>{d.date}</td>
                        <td>{d.time}</td>
                        <td>{r.ph}</td>
                        <td>{r.tds}</td>
                        <td>{r.temperature}</td>
                        <td>{r.turbidity}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section
        className={`dashboard-card admin-panel-pane admin-predictions-panel ${panelIndex === 1 ? "active" : ""}`}
        style={{ marginBottom: "1.5rem", overflowX: "auto", display: panelIndex === 1 ? "block" : "none" }}
        aria-hidden={panelIndex !== 1}
      >
        <h2 className="dashboard-section-title">Predictions</h2>
        <PeriodSelectorBar
          periodType={periodType}
          setPeriodType={setPeriodType}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          selectedYear={selectedYear}
          setSelectedYear={setSelectedYear}
          selectedWeek={selectedWeek}
          setSelectedWeek={setSelectedWeek}
          selectedMonth={selectedMonth}
          setSelectedMonth={setSelectedMonth}
          onApply={handleApplyPeriod}
          onDownloadPdf={handleDownloadPredictionsPDF}
          onDownloadCsv={handleDownloadPredictionsCsv}
          onDownloadExcel={handleDownloadPredictionsExcel}
          loading={loadingReadings || loadingPredictions || loadingLogs}
          variant="light"
        />
        {loadingPredictions ? (
          <p className="admin-predictions-loading">Loading…</p>
        ) : (
          <div className="admin-predictions-table-wrap">
              <table className="admin-predictions-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Reading</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>pH</th>
                    <th>Sugar %</th>
                    <th>Citric %</th>
                    <th>Ascorbic %</th>
                    <th>Status</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.length === 0 ? (
                    <tr><td colSpan={10}>No predictions.</td></tr>
                  ) : (
                    predictions.map((p) => {
                      const reading = readings.find((r) => r.id === p.reading);
                      const statusLabel = p.authenticity_status === "authentic" ? "Authentic" : "Adulterated";
                      const dt = (() => {
                        try {
                          const d = new Date(p.timestamp);
                          return { date: format(d, "yyyy-MM-dd"), time: format(d, "HH:mm") };
                        } catch {
                          return { date: "—", time: "—" };
                        }
                      })();
                      return (
                        <tr key={p.id}>
                          <td>{p.id}</td>
                          <td>{p.reading}</td>
                          <td>{dt.date}</td>
                          <td>{dt.time}</td>
                          <td>{reading?.ph ?? "—"}</td>
                          <td>{p.predicted_sugar}</td>
                          <td>{p.predicted_citric}</td>
                          <td>{p.predicted_ascorbic}</td>
                          <td style={{ color: p.authenticity_status === "adulterated" ? "#f87171" : "#4ade80" }}>
                            {statusLabel}
                          </td>
                          <td>{formatConfidence(p.confidence)}</td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
        )}
      </section>

      {/* Defects: low-quality predictions only */}
      <section
        className={`dashboard-card admin-panel-pane admin-defects-panel ${panelIndex === 2 ? "active" : ""}`}
        style={{ overflowX: "auto", display: panelIndex === 2 ? "block" : "none" }}
        aria-hidden={panelIndex !== 2}
      >
        <h2 className="dashboard-section-title">Defects</h2>
        <PeriodSelectorBar
          periodType={periodType}
          setPeriodType={setPeriodType}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          selectedYear={selectedYear}
          setSelectedYear={setSelectedYear}
          selectedWeek={selectedWeek}
          setSelectedWeek={setSelectedWeek}
          selectedMonth={selectedMonth}
          setSelectedMonth={setSelectedMonth}
          onApply={handleApplyPeriod}
          onDownloadPdf={handleDownloadDefectsPDF}
          onDownloadCsv={handleDownloadDefectsCsv}
          onDownloadExcel={handleDownloadDefectsExcel}
          loading={loadingReadings || loadingPredictions || loadingLogs}
          variant="light"
        />
        {loadingPredictions ? (
          <p className="admin-defects-loading">Loading…</p>
        ) : (
          <div className="admin-defects-table-wrap">
            <table className="admin-defects-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>pH</th>
                  <th>Sugar %</th>
                  <th>Citric %</th>
                  <th>Ascorbic %</th>
                  <th>Issue</th>
                </tr>
              </thead>
              <tbody>
                {(() => {
                  const defects = predictions
                    .filter((p) => p.authenticity_status === "adulterated")
                    .map((p) => {
                      const r = readings.find((x) => x.id === p.reading);
                      const ph = r?.ph ?? 0;
                      const sugar = p.predicted_sugar;
                      const citric = p.predicted_citric;
                      const ascorbic = p.predicted_ascorbic;
                      const issues: string[] = [];
                      if (ph < TYPICAL_RANGES.ph.min) issues.push(`pH low (${ph.toFixed(2)})`);
                      else if (ph > TYPICAL_RANGES.ph.max) issues.push(`pH high (${ph.toFixed(2)})`);
                      if (sugar < TYPICAL_RANGES.sugar.min) issues.push(`Sugar low (${sugar.toFixed(2)}%)`);
                      else if (sugar > TYPICAL_RANGES.sugar.max) issues.push(`Sugar high (${sugar.toFixed(2)}%)`);
                      if (citric < TYPICAL_RANGES.citric.min) issues.push(`Citric low (${citric.toFixed(4)}%)`);
                      else if (citric > TYPICAL_RANGES.citric.max) issues.push(`Citric high (${citric.toFixed(4)}%)`);
                      if (ascorbic < TYPICAL_RANGES.ascorbic.min) issues.push(`Ascorbic low (${ascorbic.toFixed(4)}%)`);
                      else if (ascorbic > TYPICAL_RANGES.ascorbic.max) issues.push(`Ascorbic high (${ascorbic.toFixed(4)}%)`);
                      return {
                        id: p.id,
                        date: format(new Date(p.timestamp), "yyyy-MM-dd"),
                        time: format(new Date(p.timestamp), "HH:mm"),
                        ph: r?.ph ?? "—",
                        sugar: p.predicted_sugar,
                        citric: p.predicted_citric,
                        ascorbic: p.predicted_ascorbic,
                        issue: issues.length > 0 ? issues.join("; ") : "Out of range",
                      };
                    });
                  if (defects.length === 0) {
                    return (
                      <tr><td colSpan={8}>No low-quality defects in this period.</td></tr>
                    );
                  }
                  return defects.map((d) => (
                    <tr key={d.id}>
                      <td>{d.id}</td>
                      <td>{d.date}</td>
                      <td>{d.time}</td>
                      <td>{d.ph}</td>
                      <td>{d.sugar}</td>
                      <td>{d.citric}</td>
                      <td>{d.ascorbic}</td>
                      <td className="admin-defects-issue">{d.issue}</td>
                    </tr>
                  ));
                })()}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section
        className={`dashboard-card admin-panel-pane admin-graphs-panel ${panelIndex === 3 ? "active" : ""}`}
        style={{ display: panelIndex === 3 ? "block" : "none" }}
        aria-hidden={panelIndex !== 3}
      >
        <h2 className="dashboard-section-title">Graph</h2>
        <div className="admin-report-period-bar admin-report-period-bar--light">
          <label>
            Date:{" "}
            <input
              type="date"
              value={selectedDate}
              onClick={(event) => event.currentTarget.showPicker?.()}
              onFocus={(event) => event.currentTarget.showPicker?.()}
              onKeyDown={(event) => {
                if (event.key !== "Tab") event.preventDefault();
              }}
              onPaste={(event) => event.preventDefault()}
              onChange={(event) => handleGraphDateChange(event.target.value)}
              aria-label="Select graph date from calendar"
              style={{ cursor: "pointer" }}
            />
          </label>
          {(loadingReadings || loadingPredictions) && <span>Loading…</span>}
        </div>
        <p style={{ marginTop: "0.75rem", color: "#e2e8f0" }}>
          Trends and correlation graphs for {dateFrom} to {dateTo}
          {joinedGraphRows.length > 0 ? ` (${joinedGraphRows.length} paired samples)` : ""}.
        </p>

        {sensorGraphData.length === 0 && joinedGraphRows.length === 0 ? (
          <p style={{ color: "#e2e8f0" }}>No graph data available for this period. Select a date from the calendar.</p>
        ) : (
          <div className="admin-graphs-stack">
            {correlationCharts.map((chart) => (
              <div key={chart.title} className="admin-report-panel admin-report-chart-panel">
                <h3>
                  {chart.title}
                  {chart.r != null ? (
                    <span style={{ marginLeft: "0.5rem", fontWeight: 500, color: "#64748b", fontSize: "0.9rem" }}>
                      (r = {chart.r.toFixed(3)})
                    </span>
                  ) : null}
                </h3>
                <div className="admin-chart-container">
                  {chart.data.length === 0 ? (
                    <p style={{ padding: "1rem", color: "#64748b" }}>No paired samples in this period.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height={300}>
                      <ScatterChart margin={{ top: 12, right: 16, bottom: 12, left: 8 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          type="number"
                          dataKey="x"
                          name={chart.xLabel}
                          label={{ value: chart.xLabel, position: "insideBottom", offset: -2 }}
                        />
                        <YAxis
                          type="number"
                          dataKey="y"
                          name={chart.yLabel}
                          label={{ value: chart.yLabel, angle: -90, position: "insideLeft" }}
                        />
                        <Tooltip
                          cursor={{ strokeDasharray: "3 3" }}
                          formatter={(value: number, name: string) => [
                            typeof value === "number" ? value.toFixed(4) : value,
                            name === "x" ? chart.xLabel : chart.yLabel,
                          ]}
                        />
                        <Scatter name={chart.title} data={chart.data} fill={chart.color} />
                      </ScatterChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            ))}

            <div className="admin-report-panel admin-report-chart-panel">
              <h3>pH and Temperature (trend)</h3>
              <div className="admin-chart-container">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={sensorGraphData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="pH" stroke="#4A90E2" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="Temperature" stroke="#F5A623" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="admin-report-panel admin-report-chart-panel">
              <h3>TDS and Turbidity (trend)</h3>
              <div className="admin-chart-container">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={sensorGraphData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="TDS" stroke="#27AE60" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="Turbidity" stroke="#8B5CF6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="admin-report-panel admin-report-chart-panel">
              <h3>Predicted Composition (trend)</h3>
              <div className="admin-chart-container">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={predictionGraphData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis yAxisId="sugar" />
                    <YAxis yAxisId="acids" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Line yAxisId="sugar" type="monotone" dataKey="Sugar" stroke="#27AE60" strokeWidth={2} dot={false} />
                    <Line yAxisId="acids" type="monotone" dataKey="Citric" stroke="#F5A623" strokeWidth={2} dot={false} />
                    <Line yAxisId="acids" type="monotone" dataKey="Ascorbic" stroke="#14B8A6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="admin-report-panel admin-report-chart-panel">
              <h3>Authenticity Results</h3>
              <div className="admin-chart-container">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={authenticityGraphData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Authentic" fill="#22C55E" />
                    <Bar dataKey="Adulterated" fill="#EF4444" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
