"""
Live charts for pH and predicted Sugar %, Citric %, Ascorbic % (Phase 4.2).
Uses Plotly; last N points or last 5 min.
"""
from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _trim_readings(readings: list[dict[str, Any]], max_points: int, max_seconds: float) -> list[dict[str, Any]]:
    """Keep last max_points and only points within max_seconds of the latest timestamp_ms."""
    if not readings:
        return []
    out = list(readings)
    if len(out) > max_points:
        out = out[-max_points:]
    if max_seconds > 0 and out:
        latest_ms = out[-1].get("timestamp_ms") or 0
        cutoff_ms = latest_ms - int(max_seconds * 1000)
        out = [r for r in out if (r.get("timestamp_ms") or 0) >= cutoff_ms]
    return out


def render_live_charts(readings: list[dict[str, Any]]) -> tuple[go.Figure, go.Figure | None]:
    """
    Build two Plotly figures:
    1) pH (and optionally tds, temperature, turbidity) over time.
    2) Predicted Sugar %, Citric %, Ascorbic % over time (if keys present); else None.
    readings: list of dicts with timestamp_ms, pH, tds, temperature, turbidity,
              and optionally predicted_sugar, predicted_citric, predicted_ascorbic.
    """
    if not readings:
        fig1 = go.Figure()
        fig1.update_layout(title="pH (no data yet)", xaxis_title="Time", yaxis_title="pH")
        return fig1, None

    ts = [r.get("timestamp_ms") or 0 for r in readings]

    # Figure 1: pH (primary) and optionally other sensors
    fig1 = make_subplots(specs=[[{"secondary_y": False}]])
    fig1.add_trace(go.Scatter(x=ts, y=[r.get("pH") for r in readings], name="pH", mode="lines+markers"), secondary_y=False)
    fig1.update_layout(title="pH (live)", xaxis_title="Timestamp (ms)", yaxis_title="pH")
    fig1.update_xaxes(rangeslider_visible=False)

    # Figure 2: Predicted sugar, citric, ascorbic (if any present)
    has_ml = any(
        (r.get("predicted_sugar") is not None or r.get("predicted_citric") is not None or r.get("predicted_ascorbic") is not None)
        for r in readings
    )
    if not has_ml:
        return fig1, None

    fig2 = go.Figure()
    for key, label in [
        ("predicted_sugar", "Sugar %"),
        ("predicted_citric", "Citric acid %"),
        ("predicted_ascorbic", "Ascorbic acid %"),
    ]:
        vals = [r.get(key) for r in readings]
        if any(v is not None for v in vals):
            fig2.add_trace(go.Scatter(x=ts, y=vals, name=label, mode="lines+markers"))
    fig2.update_layout(
        title="Predicted Sugar %, Citric %, Ascorbic % (live)",
        xaxis_title="Timestamp (ms)",
        yaxis_title="%",
    )
    fig2.update_xaxes(rangeslider_visible=False)
    return fig1, fig2


def append_reading(
    readings: list[dict[str, Any]],
    new_reading: dict[str, Any],
    max_points: int = 100,
    max_seconds: float = 300,
) -> list[dict[str, Any]]:
    """Append one reading and trim to max_points / max_seconds. Returns new list."""
    out = readings + [dict(new_reading)]
    return _trim_readings(out, max_points, max_seconds)


def last_n_readings(
    readings: list[dict[str, Any]],
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Return the last `limit` readings in chronological order.
    Used for the historical mini log (Phase 4.5).
    """
    if limit <= 0 or not readings:
        return []
    return readings[-limit:]
