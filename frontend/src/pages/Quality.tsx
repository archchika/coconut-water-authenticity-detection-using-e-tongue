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
import { fetchDaily, fetchWeekly, fetchMonthly, getApiErrorMessage } from "../api/client";
import type { AggregationResponse } from "../api/types";
import { format, getISOWeek, parseISO } from "date-fns";

function AuthenticityBadge({ status }: { status: "authentic" | "adulterated" }) {
  const isAuthentic = status === "authentic";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "0.35rem 0.75rem",
        borderRadius: 9999,
        fontWeight: 700,
        fontSize: "0.95rem",
        backgroundColor: isAuthentic ? "#276749" : "#c53030",
        color: "#fff",
        textTransform: "capitalize",
      }}
      aria-label={`Authenticity: ${status}`}
    >
      {status}
    </span>
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const exportRef = useRef<HTMLDivElement | null>(null);

  const loadData = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      if (periodType === "daily") {
        setData(await fetchDaily(date));
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

  const handleDownload = async (format: "pdf" | "jpg" | "doc") => {
    if (!exportRef.current || !data || loading) return;

    const element = exportRef.current;

    const canvas = await html2canvas(element, {
      backgroundColor: "#f8f9fa",
      scale: window.devicePixelRatio > 1 ? 2 : 1.5,
    });
    const imgData = canvas.toDataURL("image/jpeg", 0.92);
    const fileBase = `ceylon-coco-quality-${periodType}-${new Date().toISOString().slice(0, 10)}`;

    if (format === "jpg") {
      const link = document.createElement("a");
      link.href = imgData;
      link.download = `${fileBase}.jpg`;
      link.click();
      return;
    }

    if (format === "pdf") {
      const pdf = new jsPDF("landscape", "mm", "a4");
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pageWidth;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      const y = Math.max(0, (pageHeight - imgHeight) / 2);
      pdf.addImage(imgData, "JPEG", 0, y, imgWidth, imgHeight);
      pdf.save(`${fileBase}.pdf`);
      return;
    }

    const htmlContent = `<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Ceylon Coco Quality Results</title>
  </head>
  <body>
    <h1>Ceylon Coco — Quality Results</h1>
    <p>Period type: ${periodType}</p>
    <img src="${imgData}" style="max-width: 100%;" alt="Quality results" />
  </body>
</html>`;

    const blob = new Blob(["\ufeff", htmlContent], { type: "application/msword" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${fileBase}.doc`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="public-quality-page">
      <section className="public-hero public-hero-sub">
        <div className="public-hero-solid">
          <h1>Quality &amp; Methodology</h1>
          <p>How we ensure authenticity and ingredient transparency</p>
        </div>
      </section>

      <section className="public-section public-quality-commitment">
        <h2>Our Commitment to Quality</h2>
        <p>
          At Ceylon Coco, quality is at the heart of everything we do. From coconut selection to final packaging, we follow strict quality control procedures to ensure purity, safety, and freshness. Our multi-stage inspection process, hygienic production practices, and advanced monitoring systems guarantee that every bottle delivers the authentic taste of natural coconut water.
        </p>
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
                onClick={() => handleDownload("jpg")}
                disabled={data.count === 0}
              >
                JPG
              </button>
              <button
                type="button"
                onClick={() => handleDownload("doc")}
                disabled={data.count === 0}
              >
                Word
              </button>
            </div>

            <div ref={exportRef}>
              <div className="public-quality-export-header">
                <div className="public-quality-export-header-logo">
                  <img src="/company-logo.png" alt="Ceylon Coco" />
                </div>
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
                <div className="dashboard-card kpi">
                  <div className="kpi-icon" style={{ background: data.status === "authentic" ? "#d1fae5" : "#fee2e2", color: data.status === "authentic" ? "#047857" : "#b91c1c" }}>◉</div>
                  <div>
                    <div className="kpi-value"><AuthenticityBadge status={data.status} /></div>
                    <div className="kpi-label">Period status</div>
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
            </div>
          </>
        )}
      </section>
    </div>
  );
}
