/**
 * Phase 6.5 / 6.6 — Admin dashboard: raw data, alerts (with resolve), system logs.
 * Adulteration alert: sound + blinking indicator when adulterated sample identified.
 * Review: modal with per-parameter graphs (pH, sugar, citric, ascorbic).
 */
import { useState, useEffect, useCallback, useMemo, useRef } from "react";
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
  ReferenceLine,
} from "recharts";
import {
  fetchReadings,
  fetchPredictions,
  fetchAlerts,
  fetchLogs,
  resolveAlert as apiResolveAlert,
  getApiErrorMessage,
} from "../api/client";
import type { SensorReadingItem, PredictionItem, AlertItem, SystemLogItem } from "../api/types";
import { format } from "date-fns";

/** Typical ranges for coconut water (for review comparison). */
const TYPICAL_RANGES = {
  ph: { min: 4.5, max: 5.5 },
  sugar: { min: 4, max: 6 },
  citric: { min: 0.08, max: 0.15 },
  ascorbic: { min: 0.05, max: 0.12 },
};

/** Play one cycle of the adulteration alarm (unique two-tone pattern). */
function playAlarmCycle() {
  try {
    const ctx = new (window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)();
    const now = ctx.currentTime;
    const gain = ctx.createGain();
    gain.connect(ctx.destination);
    gain.gain.setValueAtTime(0, now);

    const playTone = (frequency: number, start: number, duration: number) => {
      const osc = ctx.createOscillator();
      osc.connect(gain);
      osc.frequency.value = frequency;
      osc.type = "square";
      gain.gain.setValueAtTime(0.15, start);
      gain.gain.exponentialRampToValueAtTime(0.01, start + duration);
      osc.start(start);
      osc.stop(start + duration);
    };

    playTone(880, now, 0.12);
    playTone(660, now + 0.2, 0.12);
    playTone(880, now + 0.4, 0.12);
  } catch {
    // ignore if AudioContext not supported
  }
}

export default function AdminDashboard() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [readings, setReadings] = useState<SensorReadingItem[]>([]);
  const [predictions, setPredictions] = useState<PredictionItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [logs, setLogs] = useState<SystemLogItem[]>([]);
  const [loadingReadings, setLoadingReadings] = useState(false);
  const [loadingPredictions, setLoadingPredictions] = useState(false);
  const [loadingAlerts, setLoadingAlerts] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alertTypeFilter, setAlertTypeFilter] = useState("");
  const [alertResolvedFilter, setAlertResolvedFilter] = useState("");
  const [logLevelFilter, setLogLevelFilter] = useState("");
  const [logComponentFilter, setLogComponentFilter] = useState("");
  const [logSearchFilter, setLogSearchFilter] = useState("");
  const [reviewAlert, setReviewAlert] = useState<AlertItem | null>(null);
  const alarmIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

  const loadAlerts = useCallback(async () => {
    setLoadingAlerts(true);
    setError(null);
    try {
      const data = await fetchAlerts({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        type: alertTypeFilter || undefined,
        resolved: alertResolvedFilter === "" ? undefined : alertResolvedFilter === "true",
        limit: 100,
      });
      setAlerts(data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingAlerts(false);
    }
  }, [dateFrom, dateTo, alertTypeFilter, alertResolvedFilter]);

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
    loadAlerts();
    loadLogs();
  }, [loadReadings, loadPredictions, loadAlerts, loadLogs]);

  const handleResolveAlert = useCallback(
    async (id: number, resolved: boolean) => {
      setError(null);
      try {
        await apiResolveAlert(id, resolved);
        setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, resolved } : a)));
      } catch (err) {
        setError(getApiErrorMessage(err));
      }
    },
    []
  );

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

  const unresolvedCount = useMemo(() => alerts.filter((a) => !a.resolved).length, [alerts]);
  const adulterationUnresolvedCount = useMemo(
    () => alerts.filter((a) => !a.resolved && a.type === "adulteration").length,
    [alerts]
  );

  useEffect(() => {
    const shouldPlayAlarm = adulterationUnresolvedCount > 0 && reviewAlert == null;
    if (shouldPlayAlarm) {
      playAlarmCycle();
      alarmIntervalRef.current = setInterval(playAlarmCycle, 2500);
    }
    return () => {
      if (alarmIntervalRef.current != null) {
        clearInterval(alarmIntervalRef.current);
        alarmIntervalRef.current = null;
      }
    };
  }, [adulterationUnresolvedCount, reviewAlert]);

  const authenticityDonutData = useMemo(() => {
    const authentic = predictions.filter((p) => p.authenticity_status === "authentic").length;
    const adulterated = predictions.filter((p) => p.authenticity_status === "adulterated").length;
    const other = predictions.length - authentic - adulterated;
    return [
      ...(authentic > 0 ? [{ name: "Authentic", value: authentic, fill: "#276749" }] : []),
      ...(adulterated > 0 ? [{ name: "Adulterated", value: adulterated, fill: "#c53030" }] : []),
      ...(other > 0 ? [{ name: "Other", value: other, fill: "#718096" }] : []),
    ];
  }, [predictions]);

  const finalResults = useMemo(() => {
    const avgPh = readings.length > 0
      ? readings.reduce((s, r) => s + r.ph, 0) / readings.length
      : null;
    const avgSugar = predictions.length > 0
      ? predictions.reduce((s, p) => s + p.predicted_sugar, 0) / predictions.length
      : null;
    const avgCitric = predictions.length > 0
      ? predictions.reduce((s, p) => s + p.predicted_citric, 0) / predictions.length
      : null;
    const avgAscorbic = predictions.length > 0
      ? predictions.reduce((s, p) => s + p.predicted_ascorbic, 0) / predictions.length
      : null;
    return { avgPh, avgSugar, avgCitric, avgAscorbic };
  }, [readings, predictions]);

  const DONUT_COLORS = { ph: "#2563eb", sugar: "#059669", citric: "#d97706", ascorbic: "#7c3aed" };

  const phDonutData = useMemo(() => {
    const v = finalResults.avgPh ?? 0;
    const max = 7;
    return [
      { name: "pH", value: Math.min(v, max), fill: DONUT_COLORS.ph },
      { name: "", value: Math.max(0, max - v), fill: "#e2e8f0" },
    ];
  }, [finalResults.avgPh]);

  const sugarDonutData = useMemo(() => {
    const v = finalResults.avgSugar ?? 0;
    const max = 10;
    return [
      { name: "Sugar %", value: Math.min(v, max), fill: DONUT_COLORS.sugar },
      { name: "", value: Math.max(0, max - v), fill: "#e2e8f0" },
    ];
  }, [finalResults.avgSugar]);

  const citricDonutData = useMemo(() => {
    const v = finalResults.avgCitric ?? 0;
    const max = 0.2;
    return [
      { name: "Citric %", value: Math.min(v, max), fill: DONUT_COLORS.citric },
      { name: "", value: Math.max(0, max - v), fill: "#e2e8f0" },
    ];
  }, [finalResults.avgCitric]);

  const ascorbicDonutData = useMemo(() => {
    const v = finalResults.avgAscorbic ?? 0;
    const max = 0.15;
    return [
      { name: "Ascorbic %", value: Math.min(v, max), fill: DONUT_COLORS.ascorbic },
      { name: "", value: Math.max(0, max - v), fill: "#e2e8f0" },
    ];
  }, [finalResults.avgAscorbic]);

  const PANELS = ["Readings", "Predictions", "Alerts", "Logs"] as const;
  const [panelIndex, setPanelIndex] = useState(0);
  const goPrev = () => setPanelIndex((i) => Math.max(0, i - 1));
  const goNext = () => setPanelIndex((i) => Math.min(PANELS.length - 1, i + 1));

  const reviewReading = reviewAlert?.reading != null
    ? readings.find((r) => r.id === reviewAlert.reading) ?? null
    : null;
  const reviewPrediction = reviewAlert?.reading != null
    ? predictions.find((p) => p.reading === reviewAlert.reading) ?? null
    : null;

  return (
    <div className="admin-dashboard-panels">
      {adulterationUnresolvedCount > 0 && (
        <div className="admin-adulteration-alert" role="alert">
          <span className="admin-blink-dot" aria-hidden />
          <strong>Adulterated sample detected</strong> — {adulterationUnresolvedCount} unresolved alert{adulterationUnresolvedCount !== 1 ? "s" : ""}. Go to Alerts and click <strong>Review</strong> to see parameter breakdown.
        </div>
      )}
      <section className="dashboard-card" style={{ marginBottom: "1.5rem" }}>
        <h2 className="dashboard-section-title">Filters</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem 1rem", alignItems: "center" }}>
          <label>
            Date from:{" "}
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </label>
          <label>
            Date to:{" "}
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </label>
          <label>
            Status (predictions):{" "}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All</option>
              <option value="authentic">Authentic</option>
              <option value="adulterated">Adulterated</option>
            </select>
          </label>
          <button type="button" onClick={loadAll} disabled={loadingReadings || loadingPredictions || loadingAlerts || loadingLogs}>
            {loadingReadings || loadingPredictions || loadingAlerts || loadingLogs ? "Loading…" : "Apply"}
          </button>
        </div>
        {error && <p style={{ color: "#c53030", marginTop: "0.5rem" }}>{error}</p>}
      </section>

      <div className="dashboard-kpis">
        <div className="dashboard-card kpi">
          <div className="kpi-icon" style={{ background: "#dbeafe", color: "#1d4ed8" }}>📊</div>
          <div>
            <div className="kpi-value">{readings.length}</div>
            <div className="kpi-label">Readings</div>
          </div>
        </div>
        <div className="dashboard-card kpi">
          <div className="kpi-icon" style={{ background: "#e0e7ff", color: "#4338ca" }}>📈</div>
          <div>
            <div className="kpi-value">{predictions.length}</div>
            <div className="kpi-label">Predictions</div>
          </div>
        </div>
        <div className="dashboard-card kpi">
          <div className="kpi-icon" style={{ background: "#fee2e2", color: "#b91c1c" }}>⚠</div>
          <div>
            <div className="kpi-value">{unresolvedCount}</div>
            <div className="kpi-label">Unresolved alerts</div>
          </div>
        </div>
        <div className="dashboard-card kpi">
          <div className="kpi-icon" style={{ background: "#fef3c7", color: "#b45309" }}>📋</div>
          <div>
            <div className="kpi-value">{logs.length}</div>
            <div className="kpi-label">Log entries</div>
          </div>
        </div>
      </div>

      <div className="dashboard-charts-row" style={{ marginBottom: "1rem" }}>
        <div className="dashboard-card">
          <h2 className="dashboard-section-title">Authenticity (predictions)</h2>
          <div style={{ width: "100%", height: 260 }}>
            {authenticityDonutData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={authenticityDonutData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  />
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#64748b" }}>
                No predictions to show
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="admin-final-results-charts">
        <div className="dashboard-card admin-donut-card">
          <h2 className="dashboard-section-title">pH (predictions)</h2>
          <div className="admin-donut-final" style={{ color: DONUT_COLORS.ph }}>Final result: {finalResults.avgPh != null ? finalResults.avgPh.toFixed(2) : "—"}</div>
          <div style={{ width: "100%", height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={phDonutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={0}
                  dataKey="value"
                />
                <Tooltip formatter={(value: number) => [value.toFixed(2), ""]} />
                <Legend payload={[{ value: "pH", type: "square", color: DONUT_COLORS.ph }]} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="dashboard-card admin-donut-card">
          <h2 className="dashboard-section-title">Sugar (predictions)</h2>
          <div className="admin-donut-final" style={{ color: DONUT_COLORS.sugar }}>Final result: {finalResults.avgSugar != null ? `${finalResults.avgSugar.toFixed(2)}%` : "—"}</div>
          <div style={{ width: "100%", height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sugarDonutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={0}
                  dataKey="value"
                />
                <Tooltip formatter={(value: number) => [value.toFixed(2), ""]} />
                <Legend payload={[{ value: "Sugar %", type: "square", color: DONUT_COLORS.sugar }]} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="dashboard-card admin-donut-card">
          <h2 className="dashboard-section-title">Citric acid (predictions)</h2>
          <div className="admin-donut-final" style={{ color: DONUT_COLORS.citric }}>Final result: {finalResults.avgCitric != null ? `${finalResults.avgCitric.toFixed(3)}%` : "—"}</div>
          <div style={{ width: "100%", height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={citricDonutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={0}
                  dataKey="value"
                />
                <Tooltip formatter={(value: number) => [value.toFixed(3), ""]} />
                <Legend payload={[{ value: "Citric %", type: "square", color: DONUT_COLORS.citric }]} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="dashboard-card admin-donut-card">
          <h2 className="dashboard-section-title">Ascorbic acid (predictions)</h2>
          <div className="admin-donut-final" style={{ color: DONUT_COLORS.ascorbic }}>Final result: {finalResults.avgAscorbic != null ? `${finalResults.avgAscorbic.toFixed(3)}%` : "—"}</div>
          <div style={{ width: "100%", height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={ascorbicDonutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={0}
                  dataKey="value"
                />
                <Tooltip formatter={(value: number) => [value.toFixed(3), ""]} />
                <Legend payload={[{ value: "Ascorbic %", type: "square", color: DONUT_COLORS.ascorbic }]} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="admin-panel-nav">
        <button type="button" onClick={goPrev} disabled={panelIndex === 0} aria-label="Previous section">
          ← Previous
        </button>
        <div className="admin-panel-dots">
          {PANELS.map((_, i) => (
            <button
              key={i}
              type="button"
              className={`admin-panel-dot ${i === panelIndex ? "active" : ""}`}
              onClick={() => setPanelIndex(i)}
              aria-label={`Go to ${PANELS[i]}`}
              aria-current={i === panelIndex ? "true" : undefined}
            />
          ))}
        </div>
        <span className="admin-panel-counter">
          <span className="admin-panel-current">{panelIndex + 1}</span> of {PANELS.length}
        </span>
        <button type="button" onClick={goNext} disabled={panelIndex === PANELS.length - 1} aria-label="Next section">
          Next →
        </button>
      </div>

      <section
        className={`dashboard-card admin-panel-pane ${panelIndex === 0 ? "active" : ""}`}
        style={{ marginBottom: "1.5rem", overflowX: "auto" }}
        aria-hidden={panelIndex !== 0}
      >
        <h2 className="dashboard-section-title">Sensor readings</h2>
        {loadingReadings ? (
          <p>Loading…</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                <th style={{ padding: "0.5rem" }}>ID</th>
                <th style={{ padding: "0.5rem" }}>Timestamp</th>
                <th style={{ padding: "0.5rem" }}>pH</th>
                <th style={{ padding: "0.5rem" }}>TDS</th>
                <th style={{ padding: "0.5rem" }}>Temp</th>
                <th style={{ padding: "0.5rem" }}>Turbidity</th>
                <th style={{ padding: "0.5rem" }}>Device</th>
              </tr>
            </thead>
            <tbody>
              {readings.length === 0 ? (
                <tr><td colSpan={7} style={{ padding: "0.5rem" }}>No readings.</td></tr>
              ) : (
                readings.map((r) => (
                  <tr key={r.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "0.5rem" }}>{r.id}</td>
                    <td style={{ padding: "0.5rem" }}>{formatTs(r.timestamp)}</td>
                    <td style={{ padding: "0.5rem" }}>{r.ph}</td>
                    <td style={{ padding: "0.5rem" }}>{r.tds}</td>
                    <td style={{ padding: "0.5rem" }}>{r.temperature}</td>
                    <td style={{ padding: "0.5rem" }}>{r.turbidity}</td>
                    <td style={{ padding: "0.5rem" }}>{r.source_device_id ?? "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </section>

      <section
        className={`dashboard-card admin-panel-pane ${panelIndex === 1 ? "active" : ""}`}
        style={{ marginBottom: "1.5rem", overflowX: "auto" }}
        aria-hidden={panelIndex !== 1}
      >
        <h2 className="dashboard-section-title">Predictions</h2>
        {loadingPredictions ? (
          <p>Loading…</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                <th style={{ padding: "0.5rem" }}>ID</th>
                <th style={{ padding: "0.5rem" }}>Reading</th>
                <th style={{ padding: "0.5rem" }}>Timestamp</th>
                <th style={{ padding: "0.5rem" }}>Sugar %</th>
                <th style={{ padding: "0.5rem" }}>Citric %</th>
                <th style={{ padding: "0.5rem" }}>Ascorbic %</th>
                <th style={{ padding: "0.5rem" }}>Status</th>
                <th style={{ padding: "0.5rem" }}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {predictions.length === 0 ? (
                <tr><td colSpan={8} style={{ padding: "0.5rem" }}>No predictions.</td></tr>
              ) : (
                predictions.map((p) => (
                  <tr key={p.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "0.5rem" }}>{p.id}</td>
                    <td style={{ padding: "0.5rem" }}>{p.reading}</td>
                    <td style={{ padding: "0.5rem" }}>{formatTs(p.timestamp)}</td>
                    <td style={{ padding: "0.5rem" }}>{p.predicted_sugar}</td>
                    <td style={{ padding: "0.5rem" }}>{p.predicted_citric}</td>
                    <td style={{ padding: "0.5rem" }}>{p.predicted_ascorbic}</td>
                    <td style={{ padding: "0.5rem", color: p.authenticity_status === "adulterated" ? "#c53030" : "#276749" }}>
                      {p.authenticity_status}
                    </td>
                    <td style={{ padding: "0.5rem" }}>{p.confidence != null ? p.confidence.toFixed(2) : "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </section>

      {/* Phase 6.6 — Alerts with resolve action */}
      <section
        className={`dashboard-card admin-panel-pane ${panelIndex === 2 ? "active" : ""}`}
        style={{ marginBottom: "1.5rem", overflowX: "auto" }}
        aria-hidden={panelIndex !== 2}
      >
        <h2 className="dashboard-section-title">Alerts</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem 1rem", alignItems: "center", marginBottom: "0.5rem" }}>
          <label>
            Type: <input type="text" value={alertTypeFilter} onChange={(e) => setAlertTypeFilter(e.target.value)} placeholder="e.g. adulteration" style={{ width: 120 }} />
          </label>
          <label>
            Resolved:{" "}
            <select value={alertResolvedFilter} onChange={(e) => setAlertResolvedFilter(e.target.value)}>
              <option value="">All</option>
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </label>
          <button type="button" onClick={loadAlerts} disabled={loadingAlerts}>{loadingAlerts ? "Loading…" : "Load alerts"}</button>
        </div>
        {loadingAlerts ? (
          <p>Loading…</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                <th style={{ padding: "0.5rem" }}>ID</th>
                <th style={{ padding: "0.5rem" }}>Timestamp</th>
                <th style={{ padding: "0.5rem" }}>Type</th>
                <th style={{ padding: "0.5rem" }}>Message</th>
                <th style={{ padding: "0.5rem" }}>Reading</th>
                <th style={{ padding: "0.5rem" }}>Resolved</th>
                <th style={{ padding: "0.5rem" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr><td colSpan={7} style={{ padding: "0.5rem" }}>No alerts.</td></tr>
              ) : (
                alerts.map((a) => (
                  <tr key={a.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "0.5rem" }}>{a.id}</td>
                    <td style={{ padding: "0.5rem" }}>{formatTs(a.timestamp)}</td>
                    <td style={{ padding: "0.5rem" }}>{a.type}</td>
                    <td style={{ padding: "0.5rem", maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis" }} title={a.message}>{a.message}</td>
                    <td style={{ padding: "0.5rem" }}>{a.reading ?? "—"}</td>
                    <td style={{ padding: "0.5rem" }}>{a.resolved ? "Yes" : "No"}</td>
                    <td style={{ padding: "0.5rem" }}>
                      {a.reading != null && (
                        <button type="button" onClick={() => setReviewAlert(a)} style={{ padding: "0.2rem 0.5rem", fontSize: "0.85rem", marginRight: "0.35rem" }}>
                          Review
                        </button>
                      )}
                      <button type="button" onClick={() => handleResolveAlert(a.id, !a.resolved)} style={{ padding: "0.2rem 0.5rem", fontSize: "0.85rem" }}>
                        {a.resolved ? "Mark unresolved" : "Mark resolved"}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </section>

      {/* Phase 6.6 — System logs with search/filter */}
      <section
        className={`dashboard-card admin-panel-pane ${panelIndex === 3 ? "active" : ""}`}
        style={{ overflowX: "auto" }}
        aria-hidden={panelIndex !== 3}
      >
        <h2 className="dashboard-section-title">System logs</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem 1rem", alignItems: "center", marginBottom: "0.5rem" }}>
          <label>
            Level:{" "}
            <select value={logLevelFilter} onChange={(e) => setLogLevelFilter(e.target.value)}>
              <option value="">All</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </label>
          <label>
            Component: <input type="text" value={logComponentFilter} onChange={(e) => setLogComponentFilter(e.target.value)} placeholder="e.g. upload" style={{ width: 100 }} />
          </label>
          <label>
            Search: <input type="text" value={logSearchFilter} onChange={(e) => setLogSearchFilter(e.target.value)} placeholder="message" style={{ width: 140 }} />
          </label>
          <button type="button" onClick={loadLogs} disabled={loadingLogs}>{loadingLogs ? "Loading…" : "Load logs"}</button>
        </div>
        {loadingLogs ? (
          <p>Loading…</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #e2e8f0", textAlign: "left" }}>
                <th style={{ padding: "0.5rem" }}>ID</th>
                <th style={{ padding: "0.5rem" }}>Timestamp</th>
                <th style={{ padding: "0.5rem" }}>Level</th>
                <th style={{ padding: "0.5rem" }}>Component</th>
                <th style={{ padding: "0.5rem" }}>Message</th>
                <th style={{ padding: "0.5rem" }}>Metadata</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: "0.5rem" }}>No logs.</td></tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "0.5rem" }}>{log.id}</td>
                    <td style={{ padding: "0.5rem" }}>{formatTs(log.timestamp)}</td>
                    <td style={{ padding: "0.5rem", color: log.level === "ERROR" ? "#c53030" : log.level === "WARNING" ? "#b7791f" : undefined }}>{log.level}</td>
                    <td style={{ padding: "0.5rem" }}>{log.component || "—"}</td>
                    <td style={{ padding: "0.5rem", maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis" }} title={log.message}>{log.message}</td>
                    <td style={{ padding: "0.5rem", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis" }} title={JSON.stringify(log.metadata)}>
                      {Object.keys(log.metadata || {}).length ? JSON.stringify(log.metadata) : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </section>

      {reviewAlert != null && (
        <div
          className="admin-review-modal-overlay"
          onClick={(e) => e.target === e.currentTarget && setReviewAlert(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="review-modal-title"
        >
          <div className="admin-review-modal">
            <div style={{ padding: "1.25rem", borderBottom: "1px solid #e2e8f0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2 id="review-modal-title" style={{ margin: 0, fontSize: "1.15rem" }}>Review: Adulterated sample</h2>
              <button type="button" onClick={() => setReviewAlert(null)} style={{ padding: "0.35rem 0.75rem" }}>Close</button>
            </div>
            <div style={{ padding: "1.25rem" }}>
              {reviewReading != null && reviewPrediction != null ? (
                <>
                  <p style={{ margin: "0 0 1rem 0", color: "#64748b" }}>
                    Reading #{reviewReading.id} · {formatTs(reviewReading.timestamp)}. Compare sample values to typical coconut water ranges.
                  </p>
                  <div className="review-charts-grid">
                    {[
                      { key: "ph", label: "pH", value: reviewReading.ph, max: TYPICAL_RANGES.ph.max, min: TYPICAL_RANGES.ph.min },
                      { key: "sugar", label: "Sugar %", value: reviewPrediction.predicted_sugar, max: TYPICAL_RANGES.sugar.max, min: TYPICAL_RANGES.sugar.min },
                      { key: "citric", label: "Citric acid %", value: reviewPrediction.predicted_citric, max: TYPICAL_RANGES.citric.max, min: TYPICAL_RANGES.citric.min },
                      { key: "ascorbic", label: "Ascorbic acid %", value: reviewPrediction.predicted_ascorbic, max: TYPICAL_RANGES.ascorbic.max, min: TYPICAL_RANGES.ascorbic.min },
                    ].map(({ key, label, value, max, min }) => {
                      const above = value > max;
                      const below = value < min;
                      const status = above ? "Above typical" : below ? "Below typical" : "In range";
                      const barColor = above ? "#dc2626" : below ? "#f59e0b" : "#16a34a";
                      const chartMax = Math.max(max, value) * 1.15;
                      return (
                        <div key={key} className="dashboard-card" style={{ padding: "1rem" }}>
                          <div style={{ marginBottom: "0.5rem", fontWeight: 600 }}>{label}</div>
                          <div style={{ fontSize: "0.85rem", color: above ? "#dc2626" : below ? "#b45309" : "#15803d", marginBottom: "0.35rem" }}>
                            {value.toFixed(key === "ph" ? 2 : 4)} — {status}
                          </div>
                          <div style={{ width: "100%", height: 120 }}>
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart
                                data={[{ name: "Sample", value }]}
                                layout="vertical"
                                margin={{ top: 4, right: 8, left: 8, bottom: 4 }}
                              >
                                <XAxis type="number" domain={[0, chartMax]} hide />
                                <YAxis type="category" dataKey="name" width={0} hide />
                                <ReferenceLine x={max} stroke="#94a3b8" strokeDasharray="3 3" />
                                <Bar dataKey="value" fill={barColor} radius={[0, 4, 4, 0]} barSize={28} />
                                <Tooltip formatter={(v: number) => [v.toFixed(key === "ph" ? 2 : 4), label]} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                          <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Typical range: {min}–{max}</div>
                        </div>
                      );
                    })}
                  </div>
                </>
              ) : (
                <p style={{ color: "#64748b" }}>
                  Reading or prediction data not loaded. Apply filters to include this reading, then try Review again.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
