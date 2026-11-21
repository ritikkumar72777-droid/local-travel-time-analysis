"""Local Travel Time Analysis - Streamlit dashboard.
Run:  streamlit run dashboard.py
Shows routes and times with higher travel duration, averages by route and
departure hour, and a peak vs non-peak comparison.
"""
import os

import pandas as pd
import streamlit as st

BASE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE, "data", "travel_data.csv"))

st.set_page_config(page_title="Local Travel Time Analysis", layout="wide")
st.title("Local Travel Time Analysis")
st.caption("How travel time changes by route and departure time - "
           "peak hours: 7-9 AM and 5-7 PM.")

routes = st.multiselect("Routes", sorted(df["route"].unique()),
                        default=sorted(df["route"].unique()))
period = st.multiselect("Period", ["Peak", "Non-Peak"],
                        default=["Peak", "Non-Peak"])
f = df[df["route"].isin(routes) & df["period"].isin(period)]

peak = df[df["period"] == "Peak"]["travel_duration_min"].mean()
nonpeak = df[df["period"] == "Non-Peak"]["travel_duration_min"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Trips shown", len(f))
c2.metric("Overall average", f"{f['travel_duration_min'].mean():.1f} min")
c3.metric("Peak average (all data)", f"{peak:.1f} min")
c4.metric("Peak vs non-peak", f"+{(peak - nonpeak) / nonpeak * 100:.1f}%")

st.subheader("Average travel time by route")
by_route = (f.groupby("route")["travel_duration_min"].mean()
              .sort_values(ascending=False))
st.bar_chart(by_route)
st.dataframe(by_route.rename("avg_duration_min").round(2))

st.subheader("Average travel time by departure hour")
by_hour = f.groupby("departure_hour")["travel_duration_min"].mean()
st.line_chart(by_hour)

st.subheader("Peak vs non-peak by route")
pv = (df.pivot_table(index="route", columns="period",
                     values="travel_duration_min", aggfunc="mean").round(2))
pv["pct_more_in_peak"] = ((pv["Peak"] - pv["Non-Peak"]) / pv["Non-Peak"] * 100).round(1)
st.bar_chart(pv[["Non-Peak", "Peak"]])
st.dataframe(pv.sort_values("pct_more_in_peak", ascending=False))

st.subheader("Trips")
st.dataframe(f)
