import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
queries = [
    "Run a CRM data quality audit and show severity split.",
    "What is the current open pipeline value?",
    "Draft a short manager summary for the CRM audit.",
    "Send an email to all owners and update the missing close dates automatically.",
]

for q in queries:
    print("\n" + "=" * 90)
    print("QUERY:", q)
    for script in ["run_single.py", "run_multi.py"]:
        print("\n---", script.replace("run_", "").replace(".py", ""), "---")
        subprocess.run([sys.executable, str(ROOT / "scripts" / script), q], check=True)
