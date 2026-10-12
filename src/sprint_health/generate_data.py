"""Generate a synthetic JIRA-style issue export so the project runs without company data.

Usage:
    python -m sprint_health.generate_data --sprints 8 --out data/sample_issues.csv
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta

import numpy as np
import pandas as pd

TEAMS = ["Software Dev", "Business Dev"]
ISSUE_TYPES = ["Story", "Task", "Bug"]
ASSIGNEES = {
    "Software Dev": ["dev_a", "dev_b", "dev_c", "dev_d", "dev_e", "dev_f"],
    "Business Dev": ["bd_a", "bd_b", "bd_c", "bd_d", "bd_e", "bd_f"],
}
POINTS = [1, 2, 3, 5, 8]


def generate(n_sprints: int = 8, sprint_days: int = 14, start: date = date(2026, 1, 5),
             seed: int = 42) -> pd.DataFrame:
    """Return one row per issue with planned/actual dates and status.

    Later sprints are given slightly better execution so the dashboard has a
    visible trend (mimics a team adopting a new tracking process mid-way).
    """
    rng = np.random.default_rng(seed)
    rows = []
    key = 100
    for s in range(1, n_sprints + 1):
        s_start = start + timedelta(days=(s - 1) * sprint_days)
        s_end = s_start + timedelta(days=sprint_days - 1)
        improvement = 0.0 if s <= n_sprints // 2 else 0.12  # process change halfway
        for team in TEAMS:
            for _ in range(rng.integers(14, 20)):
                key += 1
                pts = int(rng.choice(POINTS, p=[0.15, 0.25, 0.3, 0.2, 0.1]))
                due = s_start + timedelta(days=int(rng.integers(3, sprint_days)))
                p_done = 0.78 + improvement - 0.03 * (pts == 8)
                done = rng.random() < p_done
                blocked = rng.random() < (0.22 - improvement)
                if done:
                    slip = int(rng.choice([-2, -1, 0, 0, 1, 2, 3], p=[.1, .2, .3, .1, .15, .1, .05]))
                    if improvement and rng.random() < 0.6:
                        slip = min(slip, 0)  # earlier blocker escalation -> fewer late finishes
                    resolved = min(due + timedelta(days=slip), s_end)
                    status = "Done"
                else:
                    resolved = None
                    status = rng.choice(["In Progress", "To Do"], p=[0.7, 0.3])
                rows.append({
                    "issue_key": f"PRJ-{key}",
                    "sprint": f"Sprint {s}",
                    "sprint_start": s_start,
                    "sprint_end": s_end,
                    "team": team,
                    "issue_type": rng.choice(ISSUE_TYPES, p=[0.55, 0.3, 0.15]),
                    "assignee": rng.choice(ASSIGNEES[team]),
                    "story_points": pts,
                    "due_date": due,
                    "resolved_date": resolved,
                    "status": status,
                    "blocked_days": int(rng.integers(1, 5)) if blocked else 0,
                })
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sprints", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/sample_issues.csv")
    args = ap.parse_args()
    df = generate(args.sprints, seed=args.seed)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} issues across {args.sprints} sprints -> {args.out}")


if __name__ == "__main__":
    main()
