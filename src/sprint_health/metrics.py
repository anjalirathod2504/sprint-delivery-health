"""Core delivery metrics computed from a JIRA-style issue export.

Every function takes the issues DataFrame and returns a tidy DataFrame,
so the same logic powers the CLI report, the Streamlit app and the tests.
"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {
    "issue_key", "sprint", "sprint_start", "sprint_end", "team", "issue_type",
    "assignee", "story_points", "due_date", "resolved_date", "status", "blocked_days",
}


def load_issues(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["sprint_start", "sprint_end", "due_date", "resolved_date"])
    validate(df)
    return df


def validate(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Issue export is missing columns: {sorted(missing)}")


def _sprint_order(df: pd.DataFrame) -> list[str]:
    return (df[["sprint", "sprint_start"]].drop_duplicates()
            .sort_values("sprint_start")["sprint"].tolist())


def sprint_summary(df: pd.DataFrame, by_team: bool = False) -> pd.DataFrame:
    """Committed vs completed points, on-time rate, carryover and blocker load per sprint."""
    d = df.copy()
    d["done"] = d["status"].eq("Done")
    d["on_time"] = d["done"] & (d["resolved_date"] <= d["due_date"])
    d["done_points"] = d["story_points"].where(d["done"], 0)
    keys = ["sprint", "team"] if by_team else ["sprint"]
    out = d.groupby(keys).agg(
        issues=("issue_key", "count"),
        committed_points=("story_points", "sum"),
        completed_points=("done_points", "sum"),
        done_issues=("done", "sum"),
        on_time_issues=("on_time", "sum"),
        blocked_issues=("blocked_days", lambda s: int((s > 0).sum())),
        blocked_days=("blocked_days", "sum"),
    ).reset_index()
    out["say_do_ratio"] = (out["completed_points"] / out["committed_points"]).round(3)
    out["on_time_rate"] = (out["on_time_issues"] / out["issues"]).round(3)
    out["carryover_issues"] = out["issues"] - out["done_issues"]
    order = {s: i for i, s in enumerate(_sprint_order(df))}
    return out.sort_values(keys, key=lambda c: c.map(order) if c.name == "sprint" else c).reset_index(drop=True)


def velocity_trend(df: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """Completed points per sprint with a rolling average used for forecasting capacity."""
    s = sprint_summary(df)[["sprint", "committed_points", "completed_points"]].copy()
    s["rolling_velocity"] = s["completed_points"].rolling(window, min_periods=1).mean().round(1)
    return s


def burndown(df: pd.DataFrame, sprint: str) -> pd.DataFrame:
    """Daily remaining points vs the ideal line for one sprint."""
    d = df[df["sprint"] == sprint]
    if d.empty:
        raise ValueError(f"Unknown sprint: {sprint}")
    start, end = d["sprint_start"].iloc[0], d["sprint_end"].iloc[0]
    days = pd.date_range(start, end, freq="D")
    total = d["story_points"].sum()
    rows = []
    for i, day in enumerate(days):
        burned = d.loc[d["resolved_date"].notna() & (d["resolved_date"] <= day), "story_points"].sum()
        ideal = total * (1 - i / (len(days) - 1))
        rows.append({"day": day.date(), "remaining": int(total - burned), "ideal": round(ideal, 1)})
    return pd.DataFrame(rows)


def blocker_hotspots(df: pd.DataFrame, top: int = 5) -> pd.DataFrame:
    """Assignees/teams losing the most days to blockers — where a PM should step in."""
    d = df[df["blocked_days"] > 0]
    return (d.groupby(["team", "assignee"])
              .agg(blocked_issues=("issue_key", "count"), blocked_days=("blocked_days", "sum"))
              .sort_values("blocked_days", ascending=False).head(top).reset_index())


def compare_periods(df: pd.DataFrame, split_sprint: int) -> dict[str, float]:
    """Before/after comparison around a process change (e.g. new standup + tracking cadence).

    Returns percentage-point change in on-time rate and percent change in blocked days per sprint.
    """
    s = sprint_summary(df)
    s["n"] = s["sprint"].str.extract(r"(\d+)").astype(int)
    before, after = s[s["n"] <= split_sprint], s[s["n"] > split_sprint]
    if before.empty or after.empty:
        raise ValueError("split_sprint must leave sprints on both sides")
    on_time_b = before["on_time_issues"].sum() / before["issues"].sum()
    on_time_a = after["on_time_issues"].sum() / after["issues"].sum()
    blk_b, blk_a = before["blocked_days"].mean(), after["blocked_days"].mean()
    return {
        "on_time_rate_before": round(on_time_b, 3),
        "on_time_rate_after": round(on_time_a, 3),
        "on_time_change_pct": round((on_time_a - on_time_b) / on_time_b * 100, 1),
        "blocked_days_change_pct": round((blk_a - blk_b) / blk_b * 100, 1),
        "say_do_before": round(before["completed_points"].sum() / before["committed_points"].sum(), 3),
        "say_do_after": round(after["completed_points"].sum() / after["committed_points"].sum(), 3),
    }
