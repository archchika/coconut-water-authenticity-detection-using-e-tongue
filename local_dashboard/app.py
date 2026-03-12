"""
E-Tongue Local Monitoring Dashboard (Phase 4.1 + 4.2)
Streamlit app; data source from config; live charts for pH and predicted Sugar/Citric/Ascorbic %.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from config_loader import load_config, get_data_source_config, get_graphs_config
from data_source import fetch_latest_reading
from components.charts import render_live_charts, append_reading, last_n_readings
from state_names import state_to_display_label
from streamlit_autorefresh import st_autorefresh

# Page config
st.set_page_config(
    page_title="E-Tongue Local Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load config
try:
    config = load_config(Path(__file__).parent / "config.yaml")
    ds = get_data_source_config(config)
    gr = get_graphs_config(config)
    DATA_URL = ds.get("url", "http://127.0.0.1:5000/api/current")
    REFRESH_INTERVAL_SEC = int(ds.get("refresh_interval_sec", 3))
    TIMEOUT_SEC = float(ds.get("timeout_sec", 5))
    MAX_POINTS = int(gr.get("max_points", 100))
    MAX_SECONDS = float(gr.get("max_seconds", 300))
except FileNotFoundError:
    DATA_URL = "http://127.0.0.1:5000/api/current"
    REFRESH_INTERVAL_SEC = 3
    TIMEOUT_SEC = 5.0
    MAX_POINTS = 100
    MAX_SECONDS = 300.0

# Session state: rolling buffer of readings for live graphs
if "readings" not in st.session_state:
    st.session_state.readings = []

# Auto-refresh (Phase 4.6): rerun every refresh_interval_sec to poll data source
st_autorefresh(interval=REFRESH_INTERVAL_SEC * 1000, key="datarefresh")

# Sidebar: data source info
st.sidebar.header("Data source")
st.sidebar.text(f"URL: {DATA_URL}")
st.sidebar.text(f"Refresh: {REFRESH_INTERVAL_SEC} s")
st.sidebar.caption(f"Graphs: last {MAX_POINTS} points / {MAX_SECONDS:.0f} s")
st.sidebar.success(f"Auto-refresh: ON, every {REFRESH_INTERVAL_SEC} s")

# Fetch latest and append to buffer
reading = fetch_latest_reading(DATA_URL, timeout_sec=TIMEOUT_SEC)
if reading:
    st.session_state.readings = append_reading(
        st.session_state.readings, reading, max_points=MAX_POINTS, max_seconds=MAX_SECONDS
    )

# Main
st.title("E-Tongue Local Monitor")
st.caption("Phase 4.6 — Final reading, alerts, historical log, live graphs, system state, auto-refresh")

# System state display (Phase 4.6 / 4.10): aligned with firmware state names (state_names.py)
raw_state = (reading.get("system_state") or reading.get("state")) if reading else None
current_state = state_to_display_label(raw_state, has_reading=bool(reading))

st.subheader("System state")
st.metric("Current state", current_state, help="From device/gateway when system_state or state is provided; otherwise inferred.")
st.sidebar.metric("System state", current_state)

# Final averaged reading display (Phase 4.3): latest 3-read / fusion values, clearly shown
st.subheader("Final averaged reading")
if reading:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("pH", f"{reading.get('pH', 0):.2f}", help="Latest averaged pH")
    with c2:
        st.metric("TDS (ppm)", f"{reading.get('tds', 0):.1f}", help="Latest averaged TDS")
    with c3:
        st.metric("Temperature (°C)", f"{reading.get('temperature', 0):.1f}", help="Latest averaged temperature")
    with c4:
        st.metric("Turbidity", f"{reading.get('turbidity', 0):.1f}", help="Latest averaged turbidity")
    # ML predictions if present
    if any(reading.get(k) is not None for k in ("predicted_sugar", "predicted_citric", "predicted_ascorbic")):
        st.caption("Predicted (from ML)")
        c5, c6, c7 = st.columns(3)
        with c5:
            st.metric("Sugar %", f"{reading.get('predicted_sugar', 0):.2f}" if reading.get("predicted_sugar") is not None else "—")
        with c6:
            st.metric("Citric acid %", f"{reading.get('predicted_citric', 0):.2f}" if reading.get("predicted_citric") is not None else "—")
        with c7:
            st.metric("Ascorbic acid %", f"{reading.get('predicted_ascorbic', 0):.2f}" if reading.get("predicted_ascorbic") is not None else "—")
    ts = reading.get("timestamp_ms")
    st.caption(f"Timestamp: {ts} ms" if ts is not None else "No timestamp")
else:
    st.info("No reading yet. Connect the data source to see the final averaged values here.")

# Alert panel and alarm indicator (Phase 4.4)
st.subheader("Alert status")
if reading:
    status = str(reading.get("status", "")).lower()
    authenticity = str(reading.get("authenticity", "")).lower()
    alert_active = False
    alert_message = "No alert information from device."

    if status in ("threshold_alert", "adulterated"):
        alert_active = True
        if status == "threshold_alert":
            alert_message = "Sensor thresholds exceeded – possible abnormal sample. Check readings and cleaning cycle."
        else:
            alert_message = "Sample classified as ADULTERATED by ML pipeline."
    elif authenticity == "adulterated":
        alert_active = True
        alert_message = "Sample classified as ADULTERATED by ML pipeline."
    else:
        alert_message = "All values within configured safe / natural ranges (as reported by device or ML)."

    if alert_active:
        st.error(f"ALERT: {alert_message}")
        st.sidebar.error("Alarm: ACTIVE")
    else:
        st.success(alert_message)
        st.sidebar.success("Alarm: normal")
else:
    st.info("No reading yet — alert status not available.")
    st.sidebar.info("Alarm: waiting for first reading")

# Historical mini log (Phase 4.5): last 20–50 readings with timestamp and authenticity
MINI_LOG_SIZE = 50
st.subheader("Historical mini log")
mini_log = last_n_readings(st.session_state.readings, limit=MINI_LOG_SIZE)
if mini_log:
    log_rows = [
        {
            "Timestamp (ms)": r.get("timestamp_ms"),
            "pH": round(r.get("pH", 0), 2) if r.get("pH") is not None else None,
            "TDS": round(r.get("tds", 0), 1) if r.get("tds") is not None else None,
            "Temp (°C)": round(r.get("temperature", 0), 1) if r.get("temperature") is not None else None,
            "Turbidity": round(r.get("turbidity", 0), 1) if r.get("turbidity") is not None else None,
            "Status": r.get("status") or "—",
            "Authenticity": r.get("authenticity") or "—",
        }
        for r in mini_log
    ]
    st.dataframe(pd.DataFrame(log_rows), use_container_width=True, height=300)
    st.caption(f"Last {len(mini_log)} readings (newest at bottom).")
else:
    st.info("No readings yet. Data will appear here as the data source is polled.")

# Live graphs (Phase 4.2)
st.subheader("Live graphs")
fig_ph, fig_ml = render_live_charts(st.session_state.readings)
st.plotly_chart(fig_ph, use_container_width=True)
if fig_ml is not None:
    st.plotly_chart(fig_ml, use_container_width=True)
else:
    st.info("Predicted Sugar %, Citric %, Ascorbic % will appear here when the data source includes them (Phase 3).")

# Latest reading (collapsible)
with st.expander("Latest reading (raw)"):
    if reading:
        st.success("Data source connected")
        st.json(reading)
    else:
        st.warning("No data yet. Start the local server that serves the latest reading at the URL above.")
        st.info("Expected JSON: pH, tds, temperature, turbidity, timestamp_ms, status.")

if st.button("Refresh"):
    st.rerun()
