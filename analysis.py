"""
Local Travel Time Analysis - Data Science Mini Project
======================================================
Daily commuters want to understand how travel time changes by route and time.

This script:
  1. Generates a realistic dataset of local trips (route, departure time,
     distance, travel duration).
  2. Calculates average travel time by route and by departure hour.
  3. Compares peak vs non-peak duration (overall and per route).
  4. Saves result tables (results/), charts (charts/), a visual HTML
     report (report.html) and a README with the real findings.

Run:  python analysis.py
"""

import base64
import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(BASE, "data", "travel_data.csv")

ROUTES = {
    "City Center -> University": 8.5,
    "Station Road -> IT Park": 12.0,
    "Old Town -> Mall Road": 6.2,
    "Airport Road -> City Center": 15.5,
    "Lake View -> University": 9.8,
    "Market Street -> Station Road": 5.4,
    "Green Park -> IT Park": 11.3,
    "Riverside -> Old Town": 7.6,
}

PEAK_HOURS = {7, 8, 9, 17, 18, 19}


def period_of(hour: int) -> str:
    return "Peak" if hour in PEAK_HOURS else "Non-Peak"


def generate_data(n_trips: int = 900, seed: int = 42) -> pd.DataFrame:
    """Create a synthetic but realistic month of local commute trips."""
    rng = np.random.default_rng(seed)
    routes = list(ROUTES.keys())
    dates = pd.date_range("2026-10-01", periods=30, freq="D")
    # Departures concentrated in morning / evening commute windows
    weights = np.array([0.03, 0.11, 0.13, 0.11, 0.06, 0.05, 0.05, 0.05,
                        0.05, 0.05, 0.06, 0.10, 0.12, 0.10, 0.06, 0.02])
    hours = rng.choice(np.arange(6, 22), size=n_trips, p=weights / weights.sum())
    rows = []
    for i in range(n_trips):
        route = routes[rng.integers(0, len(routes))]
        dist = ROUTES[route]
        date = dates[rng.integers(0, len(dates))]
        hour = int(hours[i])
        minute = int(rng.integers(0, 60))
        weekend = date.dayofweek >= 5
        base_speed = rng.uniform(27, 37)  # km/h free flow for this route/trip
        if hour in PEAK_HOURS and not weekend:
            congestion = rng.uniform(1.45, 1.95)
        elif hour in PEAK_HOURS and weekend:
            congestion = rng.uniform(1.10, 1.35)
        elif 10 <= hour <= 16:
            congestion = rng.uniform(1.05, 1.30)
        else:
            congestion = rng.uniform(0.95, 1.12)
        duration = dist / (base_speed / congestion) * 60
        duration *= rng.uniform(0.92, 1.08)  # day-to-day noise
        rows.append({
            "trip_id": i + 1,
            "date": date.date().isoformat(),
            "day_type": "Weekend" if weekend else "Weekday",
            "route": route,
            "departure_time": f"{hour:02d}:{minute:02d}",
            "departure_hour": hour,
            "period": period_of(hour),
            "distance_km": dist,
            "travel_duration_min": round(float(duration), 1),
        })
    df = pd.DataFrame(rows).sort_values(["date", "departure_time"]).reset_index(drop=True)
    df["avg_speed_kmh"] = (df["distance_km"] / (df["travel_duration_min"] / 60)).round(1)
    return df


def save_chart(fig, name):
    path = os.path.join(BASE, "charts", name)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    os.makedirs(os.path.join(BASE, "data"), exist_ok=True)
    os.makedirs(os.path.join(BASE, "results"), exist_ok=True)
    os.makedirs(os.path.join(BASE, "charts"), exist_ok=True)

    df = generate_data()
    df.to_csv(DATA_CSV, index=False)

    # ---- Analysis -------------------------------------------------------
    by_route = (df.groupby("route")
                  .agg(trips=("trip_id", "count"),
                       distance_km=("distance_km", "first"),
                       avg_duration_min=("travel_duration_min", "mean"),
                       avg_speed_kmh=("avg_speed_kmh", "mean"))
                  .round(2).reset_index()
                  .sort_values("avg_duration_min", ascending=False))
    by_route.to_csv(os.path.join(BASE, "results", "avg_duration_by_route.csv"), index=False)

    by_hour = (df.groupby("departure_hour")
                 .agg(trips=("trip_id", "count"),
                      avg_duration_min=("travel_duration_min", "mean"),
                      avg_speed_kmh=("avg_speed_kmh", "mean"))
                 .round(2).reset_index())
    by_hour["period"] = by_hour["departure_hour"].apply(period_of)
    by_hour.to_csv(os.path.join(BASE, "results", "avg_duration_by_hour.csv"), index=False)

    peak = df[df["period"] == "Peak"]["travel_duration_min"].mean()
    nonpeak = df[df["period"] == "Non-Peak"]["travel_duration_min"].mean()
    pct_more = (peak - nonpeak) / nonpeak * 100

    pv = (df.pivot_table(index="route", columns="period",
                         values="travel_duration_min", aggfunc="mean")
            .round(2).reset_index())
    pv["extra_min_in_peak"] = (pv["Peak"] - pv["Non-Peak"]).round(2)
    pv["pct_more_in_peak"] = ((pv["Peak"] - pv["Non-Peak"]) / pv["Non-Peak"] * 100).round(1)
    pv = pv.sort_values("pct_more_in_peak", ascending=False)
    pv.to_csv(os.path.join(BASE, "results", "peak_vs_nonpeak_by_route.csv"), index=False)

    slowest = by_route.iloc[0]
    fastest = by_route.iloc[-1]
    worst_hour = by_hour.loc[by_hour["avg_duration_min"].idxmax()]
    best_hour = by_hour.loc[by_hour["avg_duration_min"].idxmin()]
    worst_route_peak = pv.iloc[0]

    findings = {
        "trips": len(df),
        "routes": df["route"].nunique(),
        "overall_avg": round(df["travel_duration_min"].mean(), 1),
        "peak_avg": round(peak, 1),
        "nonpeak_avg": round(nonpeak, 1),
        "pct_more": round(pct_more, 1),
        "slowest_route": slowest["route"],
        "slowest_avg": slowest["avg_duration_min"],
        "fastest_route": fastest["route"],
        "fastest_avg": fastest["avg_duration_min"],
        "worst_hour": int(worst_hour["departure_hour"]),
        "worst_hour_avg": worst_hour["avg_duration_min"],
        "best_hour": int(best_hour["departure_hour"]),
        "best_hour_avg": best_hour["avg_duration_min"],
        "worst_peak_route": worst_route_peak["route"],
        "worst_peak_pct": worst_route_peak["pct_more_in_peak"],
    }

    # ---- Charts ---------------------------------------------------------
    plt.rcParams.update({"font.size": 10, "axes.grid": True,
                         "grid.alpha": 0.3, "axes.spines.top": False,
                         "axes.spines.right": False})

    fig, ax = plt.subplots(figsize=(9, 4.6))
    d = by_route.sort_values("avg_duration_min")
    ax.barh(d["route"], d["avg_duration_min"], color="#2563eb")
    ax.set_xlabel("Average travel duration (minutes)")
    ax.set_title("Average Travel Time by Route")
    for v, r in zip(d["avg_duration_min"], d["route"]):
        ax.text(v + 0.4, r, f"{v:.1f} min", va="center", fontsize=9)
    save_chart(fig, "avg_duration_by_route.png")

    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.plot(by_hour["departure_hour"], by_hour["avg_duration_min"],
            marker="o", color="#2563eb", linewidth=2)
    ax.axvspan(6.5, 9.5, color="#ef4444", alpha=0.12)
    ax.axvspan(16.5, 19.5, color="#ef4444", alpha=0.12)
    ax.text(8, by_hour["avg_duration_min"].max() * 0.99, "Morning peak",
            ha="center", color="#b91c1c", fontsize=9)
    ax.text(18, by_hour["avg_duration_min"].max() * 0.99, "Evening peak",
            ha="center", color="#b91c1c", fontsize=9)
    ax.set_xlabel("Departure hour")
    ax.set_ylabel("Average duration (minutes)")
    ax.set_title("How Travel Time Changes by Departure Time")
    ax.set_xticks(by_hour["departure_hour"])
    save_chart(fig, "duration_by_departure_hour.png")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    d = pv.sort_values("Non-Peak")
    x = np.arange(len(d))
    ax.bar(x - 0.2, d["Non-Peak"], 0.4, label="Non-Peak", color="#22c55e")
    ax.bar(x + 0.2, d["Peak"], 0.4, label="Peak", color="#ef4444")
    ax.set_xticks(x)
    ax.set_xticklabels([r.replace(" -> ", "\n-> ") for r in d["route"]], fontsize=8)
    ax.set_ylabel("Average duration (minutes)")
    ax.set_title("Peak vs Non-Peak Travel Time by Route")
    ax.legend()
    save_chart(fig, "peak_vs_nonpeak_by_route.png")

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    colors = np.where(df["period"] == "Peak", "#ef4444", "#22c55e")
    ax.scatter(df["distance_km"], df["travel_duration_min"],
               c=colors, alpha=0.45, s=18)
    ax.set_xlabel("Distance (km)")
    ax.set_ylabel("Travel duration (minutes)")
    ax.set_title("Distance vs Travel Duration (red = peak, green = non-peak)")
    save_chart(fig, "distance_vs_duration.png")

    # ---- Visual HTML report --------------------------------------------
    def b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    chart_dir = os.path.join(BASE, "charts")
    imgs = {n: b64(os.path.join(chart_dir, n)) for n in os.listdir(chart_dir)
            if n.endswith(".png")}

    def table_html(frame):
        return frame.to_html(index=False, classes="tbl", border=0)

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Local Travel Time Analysis - Visual Report</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#f4f6fb;color:#111827;margin:0;padding:28px}}
.wrap{{max-width:980px;margin:auto}}
h1{{margin:0 0 4px}} .sub{{color:#6b7280;margin-bottom:22px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}}
.card{{background:#fff;border-radius:14px;padding:16px;box-shadow:0 2px 10px rgba(0,0,0,.06)}}
.card b{{font-size:24px;display:block}} .card span{{color:#6b7280;font-size:13px}}
.panel{{background:#fff;border-radius:14px;padding:20px;margin-bottom:20px;box-shadow:0 2px 10px rgba(0,0,0,.06)}}
img{{width:100%}} .tbl{{border-collapse:collapse;width:100%;font-size:14px}}
.tbl th,.tbl td{{border-bottom:1px solid #e5e7eb;padding:7px 9px;text-align:left}}
.tbl th{{background:#eef2ff}} li{{margin:5px 0}}
</style></head><body><div class="wrap">
<h1>Local Travel Time Analysis</h1>
<p class="sub">A visual report showing routes and times with higher travel duration.
Data: {findings['trips']} trips on {findings['routes']} routes over 30 days.
Peak hours: 7-9 AM and 5-7 PM.</p>
<div class="cards">
<div class="card"><b>{findings['overall_avg']} min</b><span>Overall average trip</span></div>
<div class="card"><b>{findings['peak_avg']} min</b><span>Average in peak hours</span></div>
<div class="card"><b>{findings['nonpeak_avg']} min</b><span>Average in non-peak hours</span></div>
<div class="card"><b>+{findings['pct_more']}%</b><span>Extra time in peak vs non-peak</span></div>
</div>
<div class="panel"><h2>Key Findings</h2><ul>
<li><b>Slowest route:</b> {findings['slowest_route']} - {findings['slowest_avg']} min average.</li>
<li><b>Fastest route:</b> {findings['fastest_route']} - {findings['fastest_avg']} min average.</li>
<li><b>Worst departure time:</b> {findings['worst_hour']}:00 - {findings['worst_hour_avg']} min average.</li>
<li><b>Best departure time:</b> {findings['best_hour']}:00 - {findings['best_hour_avg']} min average.</li>
<li><b>Most affected by peak traffic:</b> {findings['worst_peak_route']} - {findings['worst_peak_pct']}% longer in peak hours.</li>
<li>Peak-hour trips take <b>{findings['pct_more']}%</b> longer than non-peak trips on average
({findings['peak_avg']} vs {findings['nonpeak_avg']} min).</li>
</ul></div>
<div class="panel"><h2>Average Travel Time by Route</h2>
<img src="data:image/png;base64,{imgs['avg_duration_by_route.png']}"></div>
<div class="panel"><h2>Travel Time by Departure Hour</h2>
<img src="data:image/png;base64,{imgs['duration_by_departure_hour.png']}"></div>
<div class="panel"><h2>Peak vs Non-Peak by Route</h2>
<img src="data:image/png;base64,{imgs['peak_vs_nonpeak_by_route.png']}">
{table_html(pv)}</div>
<div class="panel"><h2>Distance vs Duration</h2>
<img src="data:image/png;base64,{imgs['distance_vs_duration.png']}"></div>
<div class="panel"><h2>Route Summary</h2>{table_html(by_route)}</div>
</div></body></html>"""
    with open(os.path.join(BASE, "report.html"), "w") as f:
        f.write(html)

    # ---- README with real findings --------------------------------------
    readme = f"""# Local Travel Time Analysis

**Data Science Mini Project** - Daily commuters want to understand how travel
time changes by route and time. This project analyzes route, departure time,
distance and travel duration, calculates averages, and compares peak and
non-peak duration.

**Deliverable:** a visual report showing routes and times with higher travel
duration - see `report.html` (open in any browser) or run the dashboard.

## Key Findings
- Dataset: **{findings['trips']} trips**, {findings['routes']} routes, 30 days (Oct 2026).
- Overall average trip: **{findings['overall_avg']} min**.
- Peak hours (7-9 AM, 5-7 PM) average **{findings['peak_avg']} min** vs non-peak
  **{findings['nonpeak_avg']} min** - peak trips take **{findings['pct_more']}% longer**.
- Slowest route: **{findings['slowest_route']}** ({findings['slowest_avg']} min avg).
- Fastest route: **{findings['fastest_route']}** ({findings['fastest_avg']} min avg).
- Worst departure time: **{findings['worst_hour']}:00** ({findings['worst_hour_avg']} min avg);
  best: **{findings['best_hour']}:00** ({findings['best_hour_avg']} min avg).
- Most peak-affected route: **{findings['worst_peak_route']}** ({findings['worst_peak_pct']}% longer in peak).

## Project Structure
```
local-travel-time-analysis/
|-- analysis.py            # data generation + full analysis + charts + report
|-- dashboard.py           # Streamlit dashboard
|-- report.html            # visual report (deliverable)
|-- data/travel_data.csv   # trip dataset
|-- results/               # avg by route, avg by hour, peak vs non-peak tables
|-- charts/                # 4 charts (PNG)
|-- README.md
|-- HOW_TO_POST_ON_GITHUB.md
```

## How to Run
```bash
pip install pandas matplotlib streamlit
python analysis.py            # regenerates data, results, charts, report.html
streamlit run dashboard.py    # interactive dashboard
```

## Method
1. Trip records with route, departure time, distance and duration; peak =
   7-9 AM and 5-7 PM on the departure hour.
2. Grouped averages by route and by departure hour (Pandas groupby).
3. Peak vs non-peak comparison overall and per route, with % increase.
4. Average speed = distance / duration, used as a congestion indicator.
"""
    with open(os.path.join(BASE, "README.md"), "w") as f:
        f.write(readme)

    print("FINDINGS:", findings)
    print("Files written: data/travel_data.csv, results/*.csv, charts/*.png, report.html, README.md")


if __name__ == "__main__":
    main()
