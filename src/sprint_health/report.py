"""Build a leadership-ready status report (Markdown + charts) from an issue export.

Usage:
    python -m sprint_health.report --input data/sample_issues.csv --split 4 --out reports
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import metrics


def _rag(on_time: float) -> str:
    return "🟢 Green" if on_time >= 0.8 else "🟡 Amber" if on_time >= 0.65 else "🔴 Red"


def build(input_csv: str, out_dir: str, split: int | None) -> Path:
    df = metrics.load_issues(input_csv)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    summary = metrics.sprint_summary(df)
    vel = metrics.velocity_trend(df)
    latest = summary.iloc[-1]

    # Chart 1: committed vs completed
    fig, ax = plt.subplots(figsize=(8, 3.6))
    x = range(len(vel))
    ax.bar([i - 0.2 for i in x], vel["committed_points"], 0.4, label="Committed", color="#9aa5b1")
    ax.bar([i + 0.2 for i in x], vel["completed_points"], 0.4, label="Completed", color="#2a9d8f")
    ax.plot(list(x), vel["rolling_velocity"], color="#264653", marker="o", label="3-sprint avg")
    ax.set_xticks(list(x), vel["sprint"], rotation=0, fontsize=8)
    ax.set_ylabel("Story points")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "velocity.png", dpi=150)
    plt.close(fig)

    # Chart 2: burndown of latest sprint
    bd = metrics.burndown(df, latest["sprint"])
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(bd["day"], bd["ideal"], "--", color="#9aa5b1", label="Ideal")
    ax.plot(bd["day"], bd["remaining"], color="#e76f51", marker=".", label="Actual")
    ax.set_title(f"Burndown — {latest['sprint']}", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out / "burndown.png", dpi=150)
    plt.close(fig)

    hot = metrics.blocker_hotspots(df)
    lines = [
        f"# Delivery Status Report — {latest['sprint']}",
        "",
        f"**Overall status:** {_rag(latest['on_time_rate'])}",
        "",
        "| Metric | Latest sprint |",
        "|---|---|",
        f"| Committed / completed points | {latest['committed_points']} / {latest['completed_points']} |",
        f"| Say/do ratio | {latest['say_do_ratio']:.0%} |",
        f"| On-time completion | {latest['on_time_rate']:.0%} |",
        f"| Carryover issues | {latest['carryover_issues']} |",
        f"| Blocked days | {latest['blocked_days']} |",
        "",
        "![Velocity](velocity.png)",
        "",
        "![Burndown](burndown.png)",
        "",
        "## Blocker hotspots (whole period)",
        "",
        hot.to_markdown(index=False),
        "",
    ]
    if split:
        c = metrics.compare_periods(df, split)
        lines += [
            f"## Before vs after process change (after Sprint {split})",
            "",
            f"- On-time rate: {c['on_time_rate_before']:.0%} → {c['on_time_rate_after']:.0%} "
            f"({c['on_time_change_pct']:+.1f}%)",
            f"- Blocked days per sprint: {c['blocked_days_change_pct']:+.1f}%",
            f"- Say/do ratio: {c['say_do_before']:.0%} → {c['say_do_after']:.0%}",
            "",
        ]
    lines += ["## Sprint-by-sprint", "", summary.to_markdown(index=False), ""]
    path = out / "status_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="data/sample_issues.csv")
    ap.add_argument("--out", default="reports")
    ap.add_argument("--split", type=int, default=None,
                    help="Sprint number after which a process change was introduced")
    args = ap.parse_args()
    print(f"Report written to {build(args.input, args.out, args.split)}")


if __name__ == "__main__":
    main()
