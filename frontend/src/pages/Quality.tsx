import { useState, useEffect, useCallback, useRef } from "react";
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Legend,
} from "recharts";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import * as XLSX from "xlsx";
import { fetchDaily, fetchDailyReadings, fetchWeekly, fetchMonthly, fetchValidationSummary, getApiErrorMessage } from "../api/client";
import type { AggregationResponse, DailyReadingRow, ValidationSummaryResponse } from "../api/types";
import { format, getISOWeek, parseISO } from "date-fns";
import { naturalReference } from "../data/naturalReference";
import { formatConfidence, confidencePercent } from "../utils/formatConfidence";

type ViewMode = "table" | "graph";

/** Prototype validation session — 100 natural + 100 artificial samples */
const VALIDATION_DEMO_DATE = "2026-06-30";

function getExportFileBase(periodType: string): string {
  return `ceylon-coco-quality-${periodType}-${new Date().toISOString().slice(0, 10)}`;
}

function fmtNum(value: number | null | undefined, digits = 4): string {
  return value != null ? value.toFixed(digits) : "";
}

function buildSummaryRows(
  data: AggregationResponse,
  reportPeriodLabel: string,
  periodType: string,
): string[][] {
  return [
    ["Ceylon Coco (Pvt) Ltd - Quality Report"],
    ["Period", reportPeriodLabel],
    ["Period type", periodType],
    [],
    ["Summary"],
    ["Total readings", String(data.count)],
    ["Authentic", String(data.authenticity.authentic)],
    ["Adulterated", String(data.authenticity.adulterated)],
    ["Overall status", data.status],
    [],
    ["Averaged readings"],
    ["pH", fmtNum(data.averages.ph)],
    ["TDS", fmtNum(data.averages.tds)],
    ["Temperature", fmtNum(data.averages.temperature)],
    ["Turbidity", fmtNum(data.averages.turbidity)],
    ["Sugar %", fmtNum(data.averages.predicted_sugar)],
    ["Citric %", fmtNum(data.averages.predicted_citric)],
    ["Ascorbic %", fmtNum(data.averages.predicted_ascorbic)],
  ];
}

const READING_HEADERS = [
  "ID",
  "Reading",
  "Date",
  "Time",
  "pH",
  "Sugar %",
  "Citric %",
  "Ascorbic %",
  "Status",
  "Confidence",
] as const;

function buildReadingRows(dailyReadings: DailyReadingRow[]): string[][] {
  const rows: string[][] = [READING_HEADERS.slice()];
  for (const row of dailyReadings) {
    rows.push([
      String(row.id),
      String(row.reading),
      row.date,
      row.time,
      row.ph.toFixed(2),
      row.predicted_sugar.toFixed(2),
      row.predicted_citric.toFixed(2),
      row.predicted_ascorbic.toFixed(2),
      row.authenticity_status === "authentic" ? "Authentic" : "Adulterated",
      row.confidence != null ? confidencePercent(row.confidence) : "",
    ]);
  }
  return rows;
}

function downloadCsv(filename: string, rows: string[][]): void {
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

function downloadExcel(
  filename: string,
  summaryRows: string[][],
  dailyReadings: DailyReadingRow[],
): void {
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(summaryRows), "Summary");
  if (dailyReadings.length > 0) {
    XLSX.utils.book_append_sheet(
      wb,
      XLSX.utils.json_to_sheet(
        dailyReadings.map((row) => ({
          ID: row.id,
          Reading: row.reading,
          Date: row.date,
          Time: row.time,
          "pH": row.ph,
          "Sugar %": row.predicted_sugar,
          "Citric %": row.predicted_citric,
          "Ascorbic %": row.predicted_ascorbic,
          Status: row.authenticity_status === "authentic" ? "Authentic" : "Adulterated",
          Confidence: row.confidence != null ? confidencePercent(row.confidence) : "",
        })),
      ),
      "Readings",
    );
  }
  XLSX.writeFile(wb, filename);
}

function NaturalVsArtificialComparison({ data }: { data: AggregationResponse | null }) {
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const params = naturalReference.parameters;
  const paramKeys = ["ph", "predicted_sugar", "predicted_citric", "predicted_ascorbic"] as const;

  const rows = paramKeys.map((key) => {
    const ref = params[key];
    if (!ref) return null;
    const ourValue = data?.averages
      ? (data.averages as unknown as Record<string, number | null>)[key] ?? null
      : null;
    const inRange =
      ourValue !== null && ourValue !== undefined
        ? ourValue >= ref.min && ourValue <= ref.max
        : null;
    return {
      key,
      label: ref.label,
      naturalRange: `${ref.min}-${ref.max} ${ref.unit}`,
      ourValue: ourValue !== null ? `${Number(ourValue).toFixed(4)} ${ref.unit}` : "\u2014",
      ourValueNum: ourValue as number | null,
      inRange,
      ref,
    };
  });

  const validRows = rows.filter((r): r is NonNullable<typeof r> => r !== null);

  // Chart data: normalize to 0-100 scale (position within natural range) for comparable display
  const chartData = validRows.map((row) => {
    const { min, max, mean, unit } = row.ref;
    const our = row.ourValueNum;
    const range = max - min;
    const naturalNorm = range > 0 ? ((mean - min) / range) * 100 : 50;
    const ourNorm = our != null && range > 0 ? ((our - min) / range) * 100 : 0;
    return {
      name: row.label,
      natural: Math.min(100, Math.max(0, naturalNorm)),
      ourProduct: ourNorm,
      inRange: row.inRange,
      min,
      max,
      unit,
      ourValue: our,
    };
  });

  return (
    <div className="dashboard-card" style={{ marginTop: "1.5rem" }}>
      <div style={{ textAlign: "center", marginBottom: "1rem" }}>
        <h3 className="dashboard-section-title" style={{ marginBottom: "0.25rem" }}>Natural vs Our Product</h3>
        <p style={{ fontSize: "0.9rem", color: "#64748b", margin: "0 auto 1rem auto", textAlign: "center", maxWidth: "42rem" }}>
          Reference values from natural coconut water (DOST PH study &amp; literature). Our product values are from E-Tongue predictions for the selected period.
        </p>
        <div style={{ display: "flex", gap: "0.5rem", justifyContent: "center", flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => setViewMode("table")}
            style={{
              padding: "0.4rem 0.75rem",
              fontSize: "0.85rem",
              borderRadius: 6,
              border: "1px solid var(--green-border)",
              background: viewMode === "table" ? "var(--green-primary)" : "#fff",
              color: viewMode === "table" ? "#fff" : "#1a1a1a",
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            Table
          </button>
          <button
            type="button"
            onClick={() => setViewMode("graph")}
            style={{
              padding: "0.4rem 0.75rem",
              fontSize: "0.85rem",
              borderRadius: 6,
              border: "1px solid var(--green-border)",
              background: viewMode === "graph" ? "var(--green-primary)" : "#fff",
              color: viewMode === "graph" ? "#fff" : "#1a1a1a",
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            Graph
          </button>
        </div>
      </div>

      {viewMode === "table" ? (
        <div style={{ overflowX: "auto" }}>
          <table className="comparison-table" style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #e2e8f0" }}>
                <th style={{ textAlign: "left", padding: "0.75rem", fontWeight: 600 }}>Parameter</th>
                <th style={{ textAlign: "left", padding: "0.75rem", fontWeight: 600 }}>Natural (reference)</th>
                <th style={{ textAlign: "left", padding: "0.75rem", fontWeight: 600 }}>Our product</th>
                <th style={{ textAlign: "center", padding: "0.75rem", fontWeight: 600 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {validRows.map((row) => (
                <tr key={row.key} style={{ borderBottom: "1px solid #e2e8f0" }}>
                  <td style={{ padding: "0.75rem" }}>{row.label}</td>
                  <td style={{ padding: "0.75rem" }}>{row.naturalRange}</td>
                  <td style={{ padding: "0.75rem" }}>{row.ourValue}</td>
                  <td style={{ padding: "0.75rem", textAlign: "center" }}>
                    {row.inRange === null ? (
                      <span style={{ color: "#94a3b8" }}>\u2014</span>
                    ) : row.inRange ? (
                      <span style={{ color: "#047857", fontWeight: 600 }}>\u2713 In range</span>
                    ) : (
                      <span style={{ color: "#b91c1c", fontWeight: 600 }}>\u2717 Out of range</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <>
          <p style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "0.5rem" }}>
            Bars show position within natural range (0% = min, 100% = max). Green = in range, red = out of range.
          </p>
          <div style={{ width: "100%", height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 80, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" domain={[-10, 110]} tickFormatter={(v) => `${v}%`} />
                <YAxis type="category" dataKey="name" width={70} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const p = payload[0].payload;
                    const ourVal = p.ourValue != null ? p.ourValue.toFixed(4) : "\u2014";
                    return (
                      <div style={{ background: "#fff", padding: "0.75rem 1rem", borderRadius: 8, boxShadow: "0 2px 8px rgba(0,0,0,0.15)", border: "1px solid #e2e8f0" }}>
                        <div style={{ fontWeight: 600, marginBottom: "0.5rem" }}>{p.name}</div>
                        <div style={{ fontSize: "0.85rem" }}>Natural range: {p.min}–{p.max} {p.unit}</div>
                        <div style={{ fontSize: "0.85rem" }}>Our product: {ourVal} {p.unit}</div>
                        <div style={{ fontSize: "0.85rem", fontWeight: 600, color: p.inRange ? "#047857" : "#b91c1c" }}>
                          {p.inRange ? "\u2713 In range" : "\u2717 Out of range"}
                        </div>
                      </div>
                    );
                  }}
                />
                <Legend />
                <Bar dataKey="natural" name="Natural (reference mean)" fill="#94a3b8" radius={[0, 4, 4, 0]} barSize={20} />
                <Bar dataKey="ourProduct" name="Our product" radius={[0, 4, 4, 0]} barSize={20}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.inRange ? "#047857" : "#b91c1c"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}

function PrototypeValidationPanel({
  summary,
  sampleCount,
}: {
  summary: ValidationSummaryResponse;
  sampleCount: number;
}) {
  return (
    <div className="dashboard-card" style={{ marginTop: "1.5rem", border: "1px solid #93c5fd", background: "#eff6ff" }}>
      <h3 className="dashboard-section-title" style={{ marginBottom: "0.5rem" }}>
        Prototype validation — {format(parseISO(summary.validation_date), "dd MMMM yyyy")}
      </h3>
      <p style={{ fontSize: "0.9rem", color: "#475569", margin: "0 0 1rem 0" }}>
        E-Tongue ML predictions vs lab reference ({summary.natural_count} natural + {summary.artificial_count} artificial samples).
        Values differ slightly from lab measurements, as expected on prototype hardware.
      </p>
      <div className="dashboard-kpis" style={{ marginBottom: "0.5rem" }}>
        <div className="dashboard-card kpi">
          <div>
            <div className="kpi-value">{summary.overall_accuracy_pct.toFixed(1)}%</div>
            <div className="kpi-label">Overall accuracy (lab vs ML)</div>
          </div>
        </div>
        <div className="dashboard-card kpi">
          <div>
            <div className="kpi-value">{summary.classification_accuracy_pct.toFixed(1)}%</div>
            <div className="kpi-label">Natural / artificial classification</div>
          </div>
        </div>
        <div className="dashboard-card kpi">
          <div>
            <div className="kpi-value">{sampleCount}</div>
            <div className="kpi-label">Readings loaded</div>
          </div>
        </div>
      </div>
      <table className="public-quality-readings-table" style={{ fontSize: "0.85rem" }}>
        <thead>
          <tr>
            <th>Parameter</th>
            <th>Accuracy vs lab</th>
            <th>MAPE</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>pH</td>
            <td>{summary.ph_accuracy_pct.toFixed(1)}%</td>
            <td>MAE {summary.ph_mae.toFixed(3)}</td>
          </tr>
          {Object.entries(summary.parameters).map(([key, val]) => (
            <tr key={key}>
              <td>{key.replace("_pct", " %")}</td>
              <td>{val.accuracy_pct.toFixed(1)}%</td>
              <td>{val.mape_pct.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Quality page — methodology text + measurement details (period selector, KPIs, graphs).
 * Measurement details (graphs etc.) are only here, not on the home page.
 */
export default function Quality() {
  const [periodType, setPeriodType] = useState<"daily" | "weekly" | "monthly">("daily");
  const [date, setDate] = useState(format(new Date(), "yyyy-MM-dd"));
  const [year, setYear] = useState(new Date().getFullYear());
  const [week, setWeek] = useState(getISOWeek(new Date()));
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [data, setData] = useState<AggregationResponse | null>(null);
  const [dailyReadings, setDailyReadings] = useState<DailyReadingRow[]>([]);
  const [validationSummary, setValidationSummary] = useState<ValidationSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const exportRef = useRef<HTMLDivElement | null>(null);

  const loadData = useCallback(async () => {
    setError(null);
    setLoading(true);
    setDailyReadings([]);
    setValidationSummary(null);
    try {
      if (periodType === "daily") {
        const requests: [
          Promise<AggregationResponse>,
          Promise<DailyReadingRow[]>,
          Promise<ValidationSummaryResponse | null>,
        ] = [
          fetchDaily(date),
          fetchDailyReadings(date),
          date === VALIDATION_DEMO_DATE
            ? fetchValidationSummary(date).catch(() => null)
            : Promise.resolve(null),
        ];
        const [agg, readings, validation] = await Promise.all(requests);
        setData(agg);
        setDailyReadings(readings);
        setValidationSummary(validation);
      } else if (periodType === "weekly") {
        setData(await fetchWeekly(year, week));
      } else {
        setData(await fetchMonthly(year, month));
      }
    } catch (err) {
      setError(getApiErrorMessage(err));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [periodType, date, year, week, month]);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const CHART_COLORS = ["#2b6cb0", "#2f855a", "#b7791f", "#805ad5"];
  const chartData = data?.averages
    ? [
        { name: "pH", value: data.averages.ph ?? 0 },
        { name: "Sugar %", value: data.averages.predicted_sugar ?? 0 },
        { name: "Citric %", value: data.averages.predicted_citric ?? 0 },
        { name: "Ascorbic %", value: data.averages.predicted_ascorbic ?? 0 },
      ].filter((d) => d.value !== undefined && d.value !== null)
    : [];

  const reportPeriodLabel =
    periodType === "daily"
      ? format(parseISO(date), "dd MMMM yyyy")
      : periodType === "weekly"
        ? `Week ${week}, ${year}`
        : format(new Date(year, month - 1, 1), "MMMM yyyy");

  const handleDownload = async (format: "pdf" | "csv" | "excel") => {
    if (!data || loading) return;

    const fileBase = getExportFileBase(periodType);
    const summaryRows = buildSummaryRows(data, reportPeriodLabel, periodType);

    const readingsForExport =
      periodType === "daily"
        ? await fetchDailyReadings(date)
        : dailyReadings;

    if (format === "csv") {
      const rows = [...summaryRows, [], ["Readings"], ...buildReadingRows(readingsForExport)];
      downloadCsv(`${fileBase}.csv`, rows);
      return;
    }

    if (format === "excel") {
      downloadExcel(`${fileBase}.xlsx`, summaryRows, readingsForExport);
      return;
    }

    const pdf = new jsPDF("portrait", "mm", "a4");
    const pageW = pdf.internal.pageSize.getWidth();
    let y = 15;

    pdf.setFontSize(16);
    const title = "Ceylon Coco Quality Report";
    pdf.text(title, (pageW - pdf.getTextWidth(title)) / 2, y);
    y += 10;
    pdf.setFontSize(10);
    pdf.text(`Period: ${reportPeriodLabel}`, 14, y);
    y += 6;
    pdf.text(`Readings: ${data.count} | Authentic: ${data.authenticity.authentic} | Adulterated: ${data.authenticity.adulterated}`, 14, y);
    y += 10;

    if (periodType === "daily" && readingsForExport.length > 0) {
      pdf.text(`All readings (${readingsForExport.length}):`, 14, y);
      y += 6;
      const colW = (pageW - 28) / 10;
      const headers = ["ID", "Reading", "Date", "Time", "pH", "Sugar", "Citric", "Ascorbic", "Status", "Conf"];
      pdf.setFont("helvetica", "bold");
      headers.forEach((h, i) => pdf.text(h, 14 + i * colW, y));
      pdf.setFont("helvetica", "normal");
      y += 6;
      for (const row of readingsForExport) {
        if (y > 270) {
          pdf.addPage();
          y = 15;
        }
        const cells = [
          String(row.id),
          String(row.reading),
          row.date,
          row.time,
          row.ph.toFixed(2),
          row.predicted_sugar.toFixed(2),
          row.predicted_citric.toFixed(2),
          row.predicted_ascorbic.toFixed(2),
          row.authenticity_status === "authentic" ? "Auth" : "Adult",
          row.confidence != null ? confidencePercent(row.confidence) : "",
        ];
        cells.forEach((v, i) => pdf.text(v.substring(0, 8), 14 + i * colW, y));
        y += 5;
      }
    } else if (exportRef.current) {
      const canvas = await html2canvas(exportRef.current, {
        backgroundColor: "#f8f9fa",
        scale: window.devicePixelRatio > 1 ? 2 : 1.5,
      });
      const imgData = canvas.toDataURL("image/jpeg", 0.92);
      const landscape = new jsPDF("landscape", "mm", "a4");
      const landscapeW = landscape.internal.pageSize.getWidth();
      const landscapeH = landscape.internal.pageSize.getHeight();
      const imgWidth = landscapeW;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      const imgY = Math.max(0, (landscapeH - imgHeight) / 2);
      landscape.addImage(imgData, "JPEG", 0, imgY, imgWidth, imgHeight);
      landscape.save(`${fileBase}.pdf`);
      return;
    }

    pdf.save(`${fileBase}.pdf`);
  };

  return (
    <div className="public-quality-page">
      <section className="public-section public-quality-commitment">
        <div className="public-quality-commitment-inner">
          <h2>Our Commitment to Quality</h2>
          <p>
            At Ceylon Coco, quality is at the heart of everything we do. From coconut selection to final packaging, we follow strict quality control procedures to ensure purity, safety, and freshness. Our multi-stage inspection process, hygienic production practices, and advanced monitoring systems guarantee that every bottle delivers the authentic taste of natural coconut water.
          </p>
        </div>
      </section>

      {/* Measurement details: period selector, KPIs, bar chart, donut chart (Quality page only) */}
      <section className="public-section">
        <h2>Measurement details</h2>
        <p style={{ marginBottom: "1rem" }}>Select a period to view readings, authenticity summary, and averaged parameters.</p>
        <div className="dashboard-controls" style={{ marginBottom: "1rem" }}>
          <label>
            Period:{" "}
            <select
              value={periodType}
              onChange={(e) => setPeriodType(e.target.value as "daily" | "weekly" | "monthly")}
            >
              <option value="daily">Day</option>
              <option value="weekly">Week</option>
              <option value="monthly">Month</option>
            </select>
          </label>
          {periodType === "daily" && (
            <label style={{ marginLeft: "1rem" }}>
              Date: <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
          )}
          {periodType === "weekly" && (
            <>
              <label style={{ marginLeft: "1rem" }}>
                Year: <input type="number" min={2020} max={2030} value={year} onChange={(e) => setYear(Number(e.target.value))} />
              </label>
              <label style={{ marginLeft: "0.5rem" }}>
                Week: <input type="number" min={1} max={53} value={week} onChange={(e) => setWeek(Number(e.target.value))} />
              </label>
            </>
          )}
          {periodType === "monthly" && (
            <>
              <label style={{ marginLeft: "1rem" }}>
                Year: <input type="number" min={2020} max={2030} value={year} onChange={(e) => setYear(Number(e.target.value))} />
              </label>
              <label style={{ marginLeft: "0.5rem" }}>
                Month: <input type="number" min={1} max={12} value={month} onChange={(e) => setMonth(Number(e.target.value))} />
              </label>
            </>
          )}
          <button type="button" onClick={loadData} disabled={loading} style={{ marginLeft: "1rem" }}>
            {loading ? "Loading…" : "Load"}
          </button>
        </div>

        {loading && (
          <div style={{ padding: "1.5rem", textAlign: "center", color: "#666" }} aria-busy="true">
            Loading…
          </div>
        )}

        {error && !loading && (
          <div style={{ padding: "1rem", background: "#fff5f5", border: "1px solid #feb2b2", borderRadius: 8, marginBottom: "1rem" }}>
            <p style={{ color: "#c53030", margin: "0 0 0.5rem 0" }}>{error}</p>
            <button type="button" onClick={loadData}>Retry</button>
          </div>
        )}

        {data && !loading && (
          <>
            <div className="public-quality-export">
              <span>Download final results:</span>
              <button
                type="button"
                onClick={() => handleDownload("pdf")}
                disabled={data.count === 0}
              >
                PDF
              </button>
              <button
                type="button"
                onClick={() => handleDownload("excel")}
                disabled={data.count === 0}
              >
                Excel
              </button>
              <button
                type="button"
                onClick={() => handleDownload("csv")}
                disabled={data.count === 0}
              >
                CSV
              </button>
            </div>

            <div ref={exportRef}>
              <div className="public-quality-export-header">
                <div className="public-quality-export-header-heading">
                  <h2 className="public-quality-export-header-title">Ceylon Coco (Pvt) Ltd</h2>
                  <p className="public-quality-export-header-sub">Quality Report of {reportPeriodLabel}</p>
                </div>
              </div>
              <div className="dashboard-kpis" style={{ marginBottom: "1.5rem" }}>
                <div className="dashboard-card kpi">
                  <div className="kpi-icon" style={{ background: "#dbeafe", color: "#1d4ed8" }}>📊</div>
                  <div>
                    <div className="kpi-value">{data.count}</div>
                    <div className="kpi-label">Readings this period</div>
                  </div>
                </div>
                <div className="dashboard-card kpi">
                  <div className="kpi-icon" style={{ background: "#d1fae5", color: "#047857" }}>✓</div>
                  <div>
                    <div className="kpi-value">{data.authenticity.authentic}</div>
                    <div className="kpi-label">Authentic</div>
                  </div>
                </div>
                <div className="dashboard-card kpi">
                  <div className="kpi-icon" style={{ background: "#fee2e2", color: "#b91c1c" }}>!</div>
                  <div>
                    <div className="kpi-value">{data.authenticity.adulterated}</div>
                    <div className="kpi-label">Adulterated</div>
                  </div>
                </div>
              </div>

              {data.count === 0 ? (
                <p style={{ color: "#666" }}>No readings for this period.</p>
              ) : (
                <div className="dashboard-charts-row">
                  <div className="dashboard-card">
                    <h3 className="dashboard-section-title">Averaged readings (pH &amp; predicted %)</h3>
                    <div style={{ width: "100%", height: 280 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip formatter={(value: number) => [Number(value).toFixed(2), ""]} />
                          <Bar dataKey="value" radius={[4, 4, 0, 0]} name="">
                            {chartData.map((_, index) => (
                              <Cell key={chartData[index].name} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  <div className="dashboard-card">
                    <h3 className="dashboard-section-title">Authenticity (this period)</h3>
                    <div style={{ width: "100%", height: 280 }}>
                      {data.authenticity.authentic + data.authenticity.adulterated > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={[
                                { name: "Authentic", value: data.authenticity.authentic, fill: "#276749" },
                                { name: "Adulterated", value: data.authenticity.adulterated, fill: "#c53030" },
                              ].filter((d) => d.value > 0)}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={90}
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
                          No authenticity breakdown for this period
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Natural vs Our Product comparison */}
              <NaturalVsArtificialComparison data={data} />

              {/* Daily readings table — only when Day is selected */}
              {periodType === "daily" && dailyReadings.length > 0 && (
                <div className="public-quality-readings-table-wrap" style={{ marginTop: "1.5rem" }}>
                  <h3 className="dashboard-section-title" style={{ marginBottom: "0.75rem" }}>Readings for {format(parseISO(date), "dd MMMM yyyy")}</h3>
                  <div style={{ overflowX: "auto", borderRadius: 8, border: "1px solid var(--green-border)", background: "#fff" }}>
                    <table className="public-quality-readings-table">
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
                        {dailyReadings.map((row) => (
                          <tr key={row.id}>
                            <td>{row.id}</td>
                            <td>{row.reading}</td>
                            <td>{row.date}</td>
                            <td>{row.time}</td>
                            <td>{row.ph.toFixed(2)}</td>
                            <td>{row.predicted_sugar.toFixed(2)}</td>
                            <td>{row.predicted_citric.toFixed(2)}</td>
                            <td>{row.predicted_ascorbic.toFixed(2)}</td>
                            <td>
                              <span style={{ color: row.authenticity_status === "authentic" ? "#047857" : "#b91c1c", fontWeight: 600 }}>
                                {row.authenticity_status === "authentic" ? "Authentic" : "Adulterated"}
                              </span>
                            </td>
                            <td>{formatConfidence(row.confidence)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
