"""Streamlit dashboard: `streamlit run app.py`

Upload your own JIRA export (same columns as data/sample_issues.csv) or use the sample.
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
from sprint_health import metrics  # noqa: E402

st.set_page_config(page_title="Sprint Delivery Health", layout="wide")
st.title("Sprint Delivery Health Dashboard")

uploaded = st.sidebar.file_uploader("JIRA issue export (CSV)", type="csv")
src = uploaded if uploaded else "data/sample_issues.csv"
df = pd.read_csv(src, parse_dates=["sprint_start", "sprint_end", "due_date", "resolved_date"])
metrics.validate(df)

teams = st.sidebar.multiselect("Teams", sorted(df["team"].unique()), default=sorted(df["team"].unique()))
df = df[df["team"].isin(teams)]

summary = metrics.sprint_summary(df)
latest = summary.iloc[-1]
prev = summary.iloc[-2] if len(summary) > 1 else latest

c1, c2, c3, c4 = st.columns(4)
c1.metric("On-time completion", f"{latest.on_time_rate:.0%}", f"{(latest.on_time_rate - prev.on_time_rate) * 100:+.0f} pts")
c2.metric("Say/do ratio", f"{latest.say_do_ratio:.0%}", f"{(latest.say_do_ratio - prev.say_do_ratio) * 100:+.0f} pts")
c3.metric("Carryover issues", int(latest.carryover_issues), int(latest.carryover_issues - prev.carryover_issues), delta_color="inverse")
c4.metric("Blocked days", int(latest.blocked_days), int(latest.blocked_days - prev.blocked_days), delta_color="inverse")

left, right = st.columns(2)
with left:
    st.subheader("Velocity")
    st.bar_chart(metrics.velocity_trend(df).set_index("sprint")[["committed_points", "completed_points"]])
with right:
    sprint = st.selectbox("Burndown for", summary["sprint"], index=len(summary) - 1)
    st.subheader(f"Burndown — {sprint}")
    st.line_chart(metrics.burndown(df, sprint).set_index("day"))

st.subheader("Blocker hotspots")
st.dataframe(metrics.blocker_hotspots(df), use_container_width=True)

st.subheader("By team")
st.dataframe(metrics.sprint_summary(df, by_team=True), use_container_width=True)

n = len(summary)
if n >= 4:
    split = st.slider("Process change introduced after sprint", 1, n - 1, n // 2)
    c = metrics.compare_periods(df, split)
    st.info(f"On-time rate {c['on_time_rate_before']:.0%} → {c['on_time_rate_after']:.0%} "
            f"({c['on_time_change_pct']:+.1f}%), blocked days per sprint {c['blocked_days_change_pct']:+.1f}%")
