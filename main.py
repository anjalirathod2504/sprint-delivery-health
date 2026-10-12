"""Run this file to run the whole project.

It creates the sample data, builds the status report and charts,
and tells you where the results are.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "src"))

from sprint_health.generate_data import generate  # noqa: E402
from sprint_health import report  # noqa: E402

df = generate(8)
df.to_csv("data/sample_issues.csv", index=False)
print(f"Step 1/2: created sample data ({len(df)} JIRA issues, 8 sprints)")

path = report.build("data/sample_issues.csv", "reports", split=4)
print("Step 2/2: built the status report")
print()
print("DONE. Results:")
print(f"  Report : {path}")
print(f"  Charts : {ROOT / 'reports' / 'velocity.png'}")
print(f"           {ROOT / 'reports' / 'burndown.png'}")
print()
print("Optional: for the interactive dashboard, run in the terminal:  streamlit run app.py")
