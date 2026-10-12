# Sprint Delivery Health Dashboard

![tests](https://github.com/anjalirathod2504/sprint-delivery-health/actions/workflows/tests.yml/badge.svg)

A Python toolkit that turns a raw JIRA issue export into the delivery metrics a program manager reports every week: **say/do ratio, on-time completion, carryover, blocker load, velocity and burndown** — plus a before/after comparison to show whether a process change actually worked.

It ships as both a **CLI report generator** (Markdown + charts for leadership updates) and an interactive **Streamlit dashboard**.

## Why I built it

Leading a 12-person team of Software Development and Business Development interns, I spent too much time assembling status updates by hand, and it was hard to prove whether new routines (structured progress reporting, earlier blocker escalation) were helping. This project automates that reporting and makes the before/after effect measurable.

## Features

| Metric | What it tells you |
|---|---|
| Say/do ratio | Completed ÷ committed story points — is the team over-committing? |
| On-time completion | Share of issues resolved by their due date |
| Carryover | Issues rolling into the next sprint |
| Blocker hotspots | Who/which team loses the most days to blockers — where to step in |
| Velocity + 3-sprint rolling avg | Capacity forecast for sprint planning |
| Burndown | Daily remaining points vs. the ideal line |
| Before/after comparison | Measures the impact of a process change at a chosen sprint |

Reports are tagged **Green / Amber / Red** for quick executive reading.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. Generate sample data (synthetic, 8 sprints, 2 teams)
PYTHONPATH=src python -m sprint_health.generate_data

# 2. Build the leadership report -> reports/status_report.md
PYTHONPATH=src python -m sprint_health.report --split 4

# 3. Launch the interactive dashboard
streamlit run app.py

# 4. Run tests
pytest
```

On Windows PowerShell use `$env:PYTHONPATH="src"` before the `python -m` commands.

## Using your own JIRA data

Export issues from JIRA as CSV and rename columns to match:

`issue_key, sprint, sprint_start, sprint_end, team, issue_type, assignee, story_points, due_date, resolved_date, status, blocked_days`

Then upload it in the dashboard sidebar or pass `--input your_file.csv` to the report.

## Sample output

With the bundled synthetic data (process change introduced after Sprint 4):

- On-time completion: **57% → 82%**
- Blocked days per sprint: **−73%**
- Say/do ratio: **80% → 86%**

![Velocity](reports/velocity.png)
![Burndown](reports/burndown.png)

> The sample data is synthetic and generated with a fixed seed; it is designed to mimic realistic sprint behaviour, not to reproduce any real team's numbers.

## Project structure

```
sprint-delivery-health/
├── app.py                      # Streamlit dashboard
├── data/sample_issues.csv      # synthetic JIRA export
├── reports/                    # generated report + charts
├── src/sprint_health/
│   ├── generate_data.py        # synthetic data generator
│   ├── metrics.py              # all metric logic (pure pandas)
│   └── report.py               # Markdown + matplotlib report builder
├── tests/test_metrics.py
├── requirements.txt
└── .github/workflows/tests.yml # CI on every push
```

## Tech

Python · pandas · NumPy · matplotlib · Streamlit · pytest · GitHub Actions
