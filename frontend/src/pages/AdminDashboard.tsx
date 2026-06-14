/**
 * Phase 6.5 / 6.6 — Admin dashboard: raw data, alerts (with resolve), system logs.
 * Adulteration alert: sound + blinking indicator when adulterated sample identified.
 * Review: modal with per-parameter graphs (pH, sugar, citric, ascorbic).
 */
import { useState, useEffect, useCallback, useMemo } from "react";
import { useLocation } from "react-router-dom";
import {
  PieChart,
  Pie,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
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
  getApiErrorMessage,
} from "../api/client";
import jsPDF from "jspdf";
import type { SensorReadingItem, PredictionItem, SystemLogItem } from "../api/types";
import { format, getISOWeek, startOfWeek, endOfWeek, startOfMonth, endOfMonth, addWeeks } from "date-fns";
import { naturalReference } from "../data/naturalReference";
import {
  cleaningInitialState,
  cleaningSensorLabels,
  cleaningChartColors,
  evaluateCleaningStatus,
  type CleaningSensorState,
} from "../data/cleaningReference";

/** Typical ranges for coconut water (for review comparison). */
const TYPICAL_RANGES = {
  ph: { min: 4.5, max: 5.5 },
  sugar: { min: 4, max: 6 },
  citric: { min: 0.08, max: 0.15 },
  ascorbic: { min: 0.05, max: 0.12 },
};

type ReadingData = { ph: number | null; citric: number | null; ascorbic: number | null; sugar: number | null; authentic?: boolean };

/** Colors for pH, citric acid, ascorbic acid, sugar (dots and charts). */
const PARAM_COLORS = { ph: "#4A90E2", citric: "#F5A623", ascorbic: "#14B8A6", sugar: "#27AE60" };

/** Sample values for Home page when no API data (demo/placeholder). */
const HOME_SAMPLE_FIRST: ReadingData = { ph: 5.10, citric: 0.13, ascorbic: 0.09, sugar: 5.00, authentic: true };
const HOME_SAMPLE_SECOND: ReadingData = { ph: 5.40, citric: 0.11, ascorbic: 0.07, sugar: 4.50, authentic: true };
const HOME_SAMPLE_THIRD: ReadingData = { ph: 5.20, citric: 0.12, ascorbic: 0.08, sugar: 4.80, authentic: true };
const HOME_SAMPLE_SUMMARY: ReadingData = { ph: 5.23, citric: 0.12, ascorbic: 0.08, sugar: 4.77 };

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
  onDownload,
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
  onDownload: () => void;
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
      <button type="button" onClick={onDownload} disabled={loading} className="admin-download-pdf-btn">
        Download
      </button>
    </div>
  );
}

/** Production report layout: Assembly Lines style (dark theme, Summary + First/Second/Third panels). */
function ProductionReportOverview({
  readings,
  predictions,
}: {
  readings: SensorReadingItem[];
  predictions: PredictionItem[];
}) {
  const readingById = useMemo(() => {
    const m = new Map<number, SensorReadingItem>();
    readings.forEach((r) => m.set(r.id, r));
    return m;
  }, [readings]);

  const lastThree = useMemo(() => {
    const arr = predictions.slice(0, 3);
    return arr.reverse();
  }, [predictions]);

  const { summary, first, second, third } = useMemo(() => {
    const rows: ReadingData[] = [];
    for (let i = 0; i < 3; i++) {
      const p = lastThree[i];
      if (!p) {
        rows.push({ ph: null, citric: null, ascorbic: null, sugar: null });
        continue;
      }
      const r = readingById.get(p.reading);
      rows.push({
        ph: r?.ph ?? null,
        citric: p.predicted_citric,
        ascorbic: p.predicted_ascorbic,
        sugar: p.predicted_sugar,
        authentic: p.authenticity_status === "authentic",
      });
    }
    const valid = rows.filter((x) => x.ph != null && x.citric != null && x.ascorbic != null && x.sugar != null);
    const summary: ReadingData =
      valid.length > 0
        ? {
            ph: valid.reduce((s, x) => s + (x.ph ?? 0), 0) / valid.length,
            citric: valid.reduce((s, x) => s + (x.citric ?? 0), 0) / valid.length,
            ascorbic: valid.reduce((s, x) => s + (x.ascorbic ?? 0), 0) / valid.length,
            sugar: valid.reduce((s, x) => s + (x.sugar ?? 0), 0) / valid.length,
          }
        : { ph: null, citric: null, ascorbic: null, sugar: null };
    const firstData = rows[0] ?? { ph: null, citric: null, ascorbic: null, sugar: null };
    const secondData = rows[1] ?? { ph: null, citric: null, ascorbic: null, sugar: null };
    const thirdData = rows[2] ?? { ph: null, citric: null, ascorbic: null, sugar: null };
    const hasData = valid.length > 0;
    return {
      summary: hasData ? summary : HOME_SAMPLE_SUMMARY,
      first: hasData ? firstData : HOME_SAMPLE_FIRST,
      second: hasData ? secondData : HOME_SAMPLE_SECOND,
      third: hasData ? thirdData : HOME_SAMPLE_THIRD,
    };
  }, [lastThree, readingById]);

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
      { name: "pH", value: v(s.ph, 7), fill: PARAM_COLORS.ph },
      { name: "Citric %", value: v(s.citric ?? 0, 0.2), fill: PARAM_COLORS.citric },
      { name: "Ascorbic %", value: v(s.ascorbic ?? 0, 0.15), fill: PARAM_COLORS.ascorbic },
      { name: "Sugar %", value: v(s.sugar ?? 0, 10), fill: PARAM_COLORS.sugar },
    ];
  }, [summary]);

  const naturalVsAverageData = useMemo(() => {
    const params = naturalReference.parameters;
    const refs = [
      { key: "ph", ref: params.ph, our: summary.ph },
      { key: "sugar", ref: params.predicted_sugar, our: summary.sugar },
      { key: "citric", ref: params.predicted_citric, our: summary.citric },
      { key: "ascorbic", ref: params.predicted_ascorbic, our: summary.ascorbic },
    ];
    const norm = (v: number, min: number, max: number) =>
      Math.max(0, Math.min(100, ((v - min) / (max - min || 0.001)) * 100));
    return refs.map(({ ref, our }) => {
      const naturalVal = ref.mean;
      const ourVal = our ?? 0;
      const min = ref.min;
      const max = ref.max;
      return {
        name: ref.label,
        natural: norm(naturalVal, min, max),
        average: norm(ourVal, min, max),
        naturalRaw: naturalVal,
        averageRaw: ourVal,
      };
    });
  }, [summary]);

  const latestSensorReading = useMemo(() => {
    if (readings.length === 0) return null;
    return [...readings].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )[0];
  }, [readings]);

  const currentCleaning: CleaningSensorState | null = latestSensorReading
    ? {
        ph: latestSensorReading.ph,
        tds: latestSensorReading.tds,
        turbidity: latestSensorReading.turbidity,
        temperature: latestSensorReading.temperature,
      }
    : null;

  const cleaningEvaluation = useMemo(() => {
    if (!currentCleaning) return null;
    return evaluateCleaningStatus(currentCleaning);
  }, [currentCleaning]);

  const cleaningChartData = useMemo(() => {
    const keys = Object.keys(cleaningInitialState) as (keyof CleaningSensorState)[];
    const ranges: Record<keyof CleaningSensorState, { min: number; max: number }> = {
      ph: { min: 6.5, max: 7.5 },
      tds: { min: 0, max: 200 },
      turbidity: { min: 0, max: 10 },
      temperature: { min: 20, max: 30 },
    };
    const norm = (v: number, min: number, max: number) =>
      Math.max(0, Math.min(100, ((v - min) / (max - min || 0.001)) * 100));
    const perSensor = cleaningEvaluation?.perSensor;
    const hasReading = currentCleaning != null;
    return keys.map((key) => ({
      name: cleaningSensorLabels[key],
      initial: norm(cleaningInitialState[key], ranges[key].min, ranges[key].max),
      current: hasReading
        ? norm(currentCleaning[key], ranges[key].min, ranges[key].max)
        : 4,
      initialRaw: cleaningInitialState[key],
      currentRaw: currentCleaning?.[key] ?? null,
      hasReading,
      matches: hasReading ? (perSensor?.[key] ?? false) : false,
    }));
  }, [currentCleaning, cleaningEvaluation]);

  const cleaningChartVerdict = cleaningEvaluation
    ? cleaningEvaluation.finished
      ? "Cleaning finished"
      : "Clean again"
    : "Awaiting sensor reading";

  /** Latest prediction verdict: one indicator lit, the other stays an empty box. */
  const authenticityStatus = useMemo((): "authentic" | "adulterated" | null => {
    if (lastThree.length === 0) return null;
    if (lastThree.some((p) => p.authenticity_status === "adulterated")) return "adulterated";
    if (lastThree.every((p) => p.authenticity_status === "authentic")) return "authentic";
    return null;
  }, [lastThree]);

  return (
    <div className="admin-report-dashboard">
      <header className="admin-report-header">
        <h1 className="admin-report-title admin-report-title-white">Coconut Water Authenticity Dashboard</h1>
      </header>

      <div className="admin-report-panels-wrap">
        <div className="admin-report-step-indicator">
          <div className="admin-report-step-item">
            <div className="admin-report-step-circle admin-report-step-circle-active">1</div>
            <span className="admin-report-step-label">First reading</span>
          </div>
          <div className="admin-report-step-connector" />
          <div className="admin-report-step-item">
            <div className="admin-report-step-circle">2</div>
            <span className="admin-report-step-label">Second reading</span>
          </div>
          <div className="admin-report-step-connector" />
          <div className="admin-report-step-item">
            <div className="admin-report-step-circle">3</div>
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
                <PieChart margin={{ top: 35, right: 20, left: 20, bottom: 55 }}>
                  <Pie
                    data={paramsPieData}
                    cx="50%"
                    cy="45%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value.toFixed(0)}`}
                  />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #475569" }} formatter={(v: number) => [v.toFixed(1), ""]} />
                  <Legend verticalAlign="bottom" layout="horizontal" wrapperStyle={{ paddingTop: "20px" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#94a3b8" }}>
                No data — values will appear when readings are available
              </div>
            )}
          </div>
        </div>
        <div className="admin-report-panel admin-report-chart-panel">
          <h3 className="admin-report-panel-title">Natural vs Average</h3>
          <p style={{ margin: "0 0 0.5rem 0", fontSize: "0.8rem", color: "#fff" }}>
            Compare natural coconut water (DOST) with our product averages
          </p>
          <div className="admin-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={naturalVsAverageData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }} barCategoryGap="20%">
                <XAxis dataKey="name" stroke="#fff" tick={{ fill: "#fff" }} />
                <YAxis stroke="#fff" tick={{ fill: "#fff" }} />
                <Tooltip
                  contentStyle={{ background: "#1e293b", border: "1px solid #475569" }}
                  formatter={(v: number, name: string, item: { payload?: { naturalRaw?: number; averageRaw?: number } }) => {
                    const raw = name === "Natural (reference)" ? item.payload?.naturalRaw : item.payload?.averageRaw;
                    const display = raw != null ? (raw < 0.01 ? raw.toFixed(4) : raw.toFixed(2)) : String(v);
                    return [display, name];
                  }}
                />
                <Legend wrapperStyle={{ color: "#fff" }} />
                <Bar dataKey="natural" name="Natural (reference)" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="average" name="Our average" fill="#22c55e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="admin-report-panel admin-report-chart-panel">
          <h3 className="admin-report-panel-title">Cleaning verification</h3>
          <div className="admin-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cleaningChartData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }} barCategoryGap="20%">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.12)" vertical={false} />
                <XAxis dataKey="name" stroke="#fff" tick={{ fill: "#fff", fontSize: 11 }} />
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
                        currentRaw?: number | null;
                        hasReading?: boolean;
                        matches?: boolean;
                      };
                    }
                  ) => {
                    const p = item.payload;
                    if (name === "Permanent reading") {
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
                <Legend wrapperStyle={{ color: "#fff" }} />
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

      <div className="admin-report-quality-indicators">
        <span className="admin-report-quality-item">
          <span
            className={`admin-report-quality-dot ${
              authenticityStatus === "authentic"
                ? "admin-report-quality-dot-active"
                : "admin-report-quality-dot-empty"
            }`}
            aria-hidden
          />
          Authentic
        </span>
        <span className="admin-report-quality-item">
          <span
            className={`admin-report-quality-dot ${
              authenticityStatus === "adulterated"
                ? "admin-report-quality-dot-active"
                : "admin-report-quality-dot-empty"
            }`}
            aria-hidden
          />
          Adulterated
        </span>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
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
        limit: 100,
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
        limit: 100,
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
        limit: 100,
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
    if (periodType === "day") {
      setDateFrom(selectedDate);
      setDateTo(selectedDate);
    } else if (periodType === "week") {
      const jan4 = new Date(selectedYear, 0, 4);
      const mondayOfWeek1 = startOfWeek(jan4, { weekStartsOn: 1 });
      const targetMonday = addWeeks(mondayOfWeek1, selectedWeek - 1);
      const start = targetMonday;
      const end = endOfWeek(targetMonday, { weekStartsOn: 1 });
      setDateFrom(format(start, "yyyy-MM-dd"));
      setDateTo(format(end, "yyyy-MM-dd"));
    } else {
      const start = startOfMonth(new Date(selectedYear, selectedMonth - 1));
      const end = endOfMonth(new Date(selectedYear, selectedMonth - 1));
      setDateFrom(format(start, "yyyy-MM-dd"));
      setDateTo(format(end, "yyyy-MM-dd"));
    }
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth]);

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateFrom, dateTo]);

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
        pdf.text("Sensor readings:", 14, y);
        y += 6;
        const colW = (pageW - 28) / 7;
        const headers = ["ID", "Date", "Time", "pH", "TDS", "Temp", "Turb"];
        pdf.setFont("helvetica", "bold");
        headers.forEach((h, i) => pdf.text(h, 14 + i * colW, y));
        pdf.setFont("helvetica", "normal");
        y += 6;
        for (const r of readings.slice(0, 30)) {
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
      y += 10;

      if (predictions.length > 0) {
        const readingById = new Map(readings.map((r) => [r.id, r]));
        const colW = (pageW - 28) / 10;
        const headers = ["ID", "Reading", "Date", "Time", "pH", "Sugar %", "Citric %", "Ascorbic %", "Status", "Conf"];
        pdf.setFont("helvetica", "bold");
        headers.forEach((h, i) => pdf.text(h, 14 + i * colW, y));
        pdf.setFont("helvetica", "normal");
        y += 6;
        for (const p of predictions.slice(0, 25)) {
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
            p.confidence != null ? p.confidence.toFixed(2) : "—",
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
  }, [periodType, selectedDate, selectedYear, selectedWeek, selectedMonth, predictions, readings]);

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

  const location = useLocation();
  const panelIndex = useMemo(() => {
    const p = location.pathname;
    if (p === "/admin/readings") return 0;
    if (p === "/admin/predictions") return 1;
    if (p === "/admin/logs") return 2;
    return -1; // Overview
  }, [location.pathname]);

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
          <ProductionReportOverview readings={readings} predictions={predictions} />
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
          onDownload={handleDownloadPDF}
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
          onDownload={handleDownloadPredictionsPDF}
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
                          <td>{p.confidence != null ? p.confidence.toFixed(2) : "—"}</td>
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
          onDownload={handleDownloadDefectsPDF}
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
    </div>
  );
}
