import pandas as pd
import pytest

from sprint_health import metrics
from sprint_health.generate_data import generate


@pytest.fixture
def tiny():
    d = pd.Timestamp
    return pd.DataFrame([
        # sprint 1: 2 issues, one done on time, one not done
        dict(issue_key="A-1", sprint="Sprint 1", sprint_start=d("2026-01-05"), sprint_end=d("2026-01-09"),
             team="T", issue_type="Story", assignee="x", story_points=3, due_date=d("2026-01-07"),
             resolved_date=d("2026-01-06"), status="Done", blocked_days=0),
        dict(issue_key="A-2", sprint="Sprint 1", sprint_start=d("2026-01-05"), sprint_end=d("2026-01-09"),
             team="T", issue_type="Task", assignee="y", story_points=5, due_date=d("2026-01-08"),
             resolved_date=pd.NaT, status="In Progress", blocked_days=2),
        # sprint 2: done late
        dict(issue_key="A-3", sprint="Sprint 2", sprint_start=d("2026-01-12"), sprint_end=d("2026-01-16"),
             team="T", issue_type="Bug", assignee="x", story_points=2, due_date=d("2026-01-13"),
             resolved_date=d("2026-01-15"), status="Done", blocked_days=0),
    ])


def test_summary_counts(tiny):
    s = metrics.sprint_summary(tiny).set_index("sprint")
    assert s.loc["Sprint 1", "committed_points"] == 8
    assert s.loc["Sprint 1", "completed_points"] == 3
    assert s.loc["Sprint 1", "on_time_rate"] == 0.5
    assert s.loc["Sprint 1", "carryover_issues"] == 1
    assert s.loc["Sprint 2", "on_time_rate"] == 0.0  # resolved after due date


def test_burndown_ends_at_remaining(tiny):
    bd = metrics.burndown(tiny, "Sprint 1")
    assert bd["remaining"].iloc[0] == 8
    assert bd["remaining"].iloc[-1] == 5
    assert bd["ideal"].iloc[-1] == 0


def test_validate_rejects_missing_columns(tiny):
    with pytest.raises(ValueError):
        metrics.validate(tiny.drop(columns=["status"]))


def test_generated_data_shows_improvement():
    c = metrics.compare_periods(generate(8, seed=1), split_sprint=4)
    assert c["on_time_rate_after"] > c["on_time_rate_before"]
    assert c["blocked_days_change_pct"] < 0
