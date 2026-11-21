# Local Travel Time Analysis

**Data Science Mini Project** - Daily commuters want to understand how travel
time changes by route and time. This project analyzes route, departure time,
distance and travel duration, calculates averages, and compares peak and
non-peak duration.

**Deliverable:** a visual report showing routes and times with higher travel
duration - see `report.html` (open in any browser) or run the dashboard.

## Key Findings
- Dataset: **900 trips**, 8 routes, 30 days (Oct 2026).
- Overall average trip: **25.1 min**.
- Peak hours (7-9 AM, 5-7 PM) average **28.6 min** vs non-peak
  **19.8 min** - peak trips take **44.4% longer**.
- Slowest route: **Airport Road -> City Center** (41.61 min avg).
- Fastest route: **Market Street -> Station Road** (14.32 min avg).
- Worst departure time: **18:00** (29.2 min avg);
  best: **14:00** (18.38 min avg).
- Most peak-affected route: **Green Park -> IT Park** (42.8% longer in peak).

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
